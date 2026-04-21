import json

from responses import error_response, success_response


class TestSuccessResponse:
    def test_status_code_is_200(self) -> None:
        assert success_response([]).status_code == 200

    def test_mimetype_is_json(self) -> None:
        assert success_response([]).mimetype == "application/json"

    def test_body_is_serialized_data(self) -> None:
        data = [{"key": "value"}]
        body = json.loads(success_response(data).get_body())
        assert body == data


class TestErrorResponse:
    def test_status_code_is_set(self) -> None:
        assert error_response("oops", 400).status_code == 400
        assert error_response("oops", 404).status_code == 404
        assert error_response("oops", 500).status_code == 500

    def test_mimetype_is_json(self) -> None:
        assert error_response("oops", 400).mimetype == "application/json"

    def test_body_contains_error_message(self) -> None:
        body = json.loads(error_response("something went wrong", 400).get_body())
        assert body == {"error": "something went wrong"}
