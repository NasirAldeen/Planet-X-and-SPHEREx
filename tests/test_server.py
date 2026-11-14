import json
import unittest
from unittest.mock import patch

import server


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.client = server.app.test_client()
        server.jobs.clear()
        server.history.clear()

    def test_health_and_static_assets(self):
        self.assertEqual(self.client.get('/api/health').json['status'], 'ok')
        for url in ['/', '/style.css', '/app.js', '/science.js', '/icon.svg', '/data/targets.json']:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertIn("object-src 'none'", response.headers['Content-Security-Policy'])
                response.close()

    def test_project_files_are_never_served(self):
        for url in ['/server.py', '/.git/config', '/.env', '/../server.py', '/data/../../server.py']:
            self.assertEqual(self.client.get(url).status_code, 404)

    def test_invalid_requests_do_not_query_archive(self):
        for body in [None, [], {'ra':360,'dec':0}, {'ra':'nan','dec':0}, {'ra':1,'dec':2,'fov':500}]:
            self.assertEqual(self.client.post('/api/search', json=body).status_code, 400)

    @patch('server.pool.submit')
    def test_jobs_are_bounded_and_private_identifiers_are_unpredictable(self, submit):
        ids = []
        for _ in range(4):
            response = self.client.post('/api/search', json={'ra':10,'dec':20})
            self.assertEqual(response.status_code,202)
            ids.append(response.json['id'])
        self.assertEqual(len(set(ids)),4)
        self.assertGreater(len(ids[0]),20)
        self.assertEqual(self.client.post('/api/search',json={'ra':10,'dec':20}).status_code,429)
        self.assertEqual(self.client.get('/api/jobs/'+ids[0]).json['status'],'running')
        self.assertEqual(self.client.get('/api/jobs/unknown').status_code,404)

    @patch('server.build_sequence', return_value={'frames':[{'date':'2026-01-01'}]})
    @patch('server.pool.submit', side_effect=lambda fn: fn())
    def test_successful_live_search_returns_processed_result(self, submit, build):
        response = self.client.post('/api/search',json={'ra':10,'dec':20,'fov':6,'detector':'D3'})
        result=self.client.get('/api/jobs/'+response.json['id']).json
        self.assertEqual(result['status'],'done')
        self.assertEqual(len(result['result']['frames']),1)
        build.assert_called_once()


if __name__ == '__main__': unittest.main()
