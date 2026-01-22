"""
测试自定义异常层次结构

验证异常的创建、to_dict()方法、以及FastAPI异常处理器的行为
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.exceptions import (
    AShareBaseException,
    DataNotFoundError,
    ValidationError,
    InvalidSymbolError,
    ExternalAPIError,
    TushareAPIError,
    DatabaseError,
    BusinessLogicError,
    InsufficientDataError,
)


class TestExceptionHierarchy:
    """测试异常层次结构"""

    def test_base_exception_creation(self):
        """测试基础异常创建"""
        exc = AShareBaseException(
            message="Test error",
            code="TEST_ERROR",
            details={"key": "value"}
        )
        assert exc.message == "Test error"
        assert exc.code == "TEST_ERROR"
        assert exc.details == {"key": "value"}

    def test_base_exception_to_dict(self):
        """测试异常转换为字典"""
        exc = AShareBaseException(
            message="Test error",
            code="TEST_ERROR",
            details={"key": "value"}
        )
        result = exc.to_dict()
        assert result == {
            "error": "TEST_ERROR",
            "message": "Test error",
            "details": {"key": "value"}
        }

    def test_data_not_found_error(self):
        """测试数据未找到异常"""
        exc = DataNotFoundError(resource="Stock", identifier="000001.SZ")
        assert exc.resource == "Stock"
        assert exc.identifier == "000001.SZ"
        assert exc.code == "DATA_NOT_FOUND"
        assert "Stock not found: 000001.SZ" in exc.message

    def test_validation_error(self):
        """测试验证错误异常"""
        exc = ValidationError(field="ticker", reason="Invalid format", value="ABC")
        assert exc.field == "ticker"
        assert exc.reason == "Invalid format"
        assert exc.code == "VALIDATION_ERROR"

    def test_invalid_symbol_error(self):
        """测试无效股票代码异常"""
        exc = InvalidSymbolError(symbol="INVALID")
        assert exc.field == "symbol"
        assert "INVALID" in str(exc.details["value"])

    def test_external_api_error(self):
        """测试外部API错误"""
        exc = ExternalAPIError(provider="TestAPI", details="Connection timeout", status_code=503)
        assert exc.provider == "TestAPI"
        assert exc.status_code == 503
        assert exc.code == "EXTERNAL_API_ERROR"

    def test_tushare_api_error(self):
        """测试Tushare API错误"""
        exc = TushareAPIError(details="Rate limit exceeded")
        assert exc.provider == "Tushare"
        assert exc.code == "EXTERNAL_API_ERROR"

    def test_database_error(self):
        """测试数据库错误"""
        exc = DatabaseError(operation="INSERT", reason="Unique constraint violation")
        assert "INSERT" in exc.message
        assert exc.code == "DATABASE_ERROR"

    def test_business_logic_error(self):
        """测试业务逻辑错误"""
        exc = BusinessLogicError(message="Invalid operation", details={"reason": "test"})
        assert exc.message == "Invalid operation"
        assert exc.details["reason"] == "test"

    def test_insufficient_data_error(self):
        """测试数据不足错误"""
        exc = InsufficientDataError(operation="MACD calculation", required=26, actual=10)
        assert "required 26" in exc.message
        assert "got 10" in exc.message


class TestExceptionHandlers:
    """测试FastAPI异常处理器"""

    @pytest.fixture
    def app(self):
        """创建测试用FastAPI应用"""
        from fastapi import Request
        from fastapi.responses import JSONResponse

        app = FastAPI()

        @app.exception_handler(DataNotFoundError)
        async def data_not_found_handler(request: Request, exc: DataNotFoundError):
            return JSONResponse(status_code=404, content=exc.to_dict())

        @app.exception_handler(ValidationError)
        async def validation_error_handler(request: Request, exc: ValidationError):
            return JSONResponse(status_code=400, content=exc.to_dict())

        @app.get("/test/not-found")
        async def test_not_found():
            raise DataNotFoundError(resource="Stock", identifier="999999")

        @app.get("/test/validation")
        async def test_validation():
            raise ValidationError(field="ticker", reason="Invalid format", value="ABC")

        return app

    @pytest.fixture
    def client(self, app):
        """创建测试客户端"""
        return TestClient(app)

    def test_data_not_found_handler(self, client):
        """测试数据未找到处理器"""
        response = client.get("/test/not-found")
        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "DATA_NOT_FOUND"
        assert "Stock not found" in data["message"]
        assert data["details"]["resource"] == "Stock"
        assert data["details"]["identifier"] == "999999"

    def test_validation_error_handler(self, client):
        """测试验证错误处理器"""
        response = client.get("/test/validation")
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_ERROR"
        assert "Invalid format" in data["message"]
        assert data["details"]["field"] == "ticker"


class TestExceptionInheritance:
    """测试异常继承关系"""

    def test_all_exceptions_inherit_from_base(self):
        """测试所有自定义异常都继承自基类"""
        exceptions = [
            DataNotFoundError("res", "id"),
            ValidationError("field", "reason"),
            ExternalAPIError("provider", "details"),
            DatabaseError("op", "reason"),
            BusinessLogicError("msg"),
        ]

        for exc in exceptions:
            assert isinstance(exc, AShareBaseException)
            assert isinstance(exc, Exception)

    def test_exception_can_be_caught_by_base_type(self):
        """测试可以用基类捕获所有自定义异常"""
        try:
            raise DataNotFoundError(resource="Test", identifier="123")
        except AShareBaseException as e:
            assert e.code == "DATA_NOT_FOUND"
        except Exception:
            pytest.fail("Should be caught by AShareBaseException")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
