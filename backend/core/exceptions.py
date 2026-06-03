"""AWS discovery error types mapped to HTTP responses."""


class AWSDiscoveryError(Exception):
    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.message = message
        self.code = code


class AWSCredentialsError(AWSDiscoveryError):
    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            detail
            or "AWS credentials are not configured. Use environment variables, "
            "~/.aws/credentials, or an IAM instance/task role.",
            "aws_credentials_not_configured",
        )


class AWSAccessDeniedError(AWSDiscoveryError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, "aws_access_denied")


class AWSRegionError(AWSDiscoveryError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, "aws_region_error")
