import unittest

from src.supplychain_tlm.router import route_request


class RouterTests(unittest.TestCase):
    def test_cross_document_release_question_routes_multiple_domains(self):
        routes = route_request("Can this shipment be released if the invoice and HS code disagree?")
        self.assertEqual([route.capability for route in routes], ["customs", "financial", "shipping"])

    def test_unknown_request_has_no_specialist_route(self):
        self.assertEqual(route_request("What is the status?"), ())


if __name__ == "__main__":
    unittest.main()
