import json
import unittest
from unittest.mock import patch

from src.supplychain_tlm.http_connectors import JSONHTTPClient, SAPHTTPConnector, WMSHTTPConnector


class FakeResponse:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps({"result": "ok"}).encode()


class HTTPConnectorTests(unittest.TestCase):
    def test_sap_connector_uses_authenticated_json_transport(self):
        client = JSONHTTPClient("https://sap.example.test/api", "secret")
        with patch("src.supplychain_tlm.http_connectors.urlopen", return_value=FakeResponse()) as open_url:
            self.assertEqual(SAPHTTPConnector(client).release_shipment("S-1", "PO-1"), "ok")
        request = open_url.call_args.args[0]
        self.assertEqual(request.full_url, "https://sap.example.test/api/sap/release")
        self.assertEqual(request.get_header("Authorization"), "Bearer secret")

    def test_wms_connector_maps_inventory_operation(self):
        client = JSONHTTPClient("https://wms.example.test", "secret")
        with patch("src.supplychain_tlm.http_connectors.urlopen", return_value=FakeResponse()) as open_url:
            self.assertEqual(WMSHTTPConnector(client).reserve_inventory("S-1", "SKU-1", 2), "ok")
        self.assertIn("/wms/reserve", open_url.call_args.args[0].full_url)

    def test_connector_rejects_empty_token_and_non_tls_remote_url(self):
        with self.assertRaisesRegex(ValueError, "token"):
            JSONHTTPClient("https://sap.example.test", "")
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            JSONHTTPClient("http://sap.example.test", "secret")


if __name__ == "__main__":
    unittest.main()
