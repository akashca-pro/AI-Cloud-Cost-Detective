from scanners.base import BaseScanner, flatten_aws_tags, tags_match
from scanners.ebs_scanner import EBSScanner
from scanners.ec2_scanner import EC2Scanner
from scanners.elb_scanner import ELBScanner
from scanners.rds_scanner import RDSScanner
from scanners.s3_scanner import S3Scanner

SCANNER_REGISTRY: dict[str, BaseScanner] = {
    "ec2": EC2Scanner(),
    "rds": RDSScanner(),
    "s3": S3Scanner(),
    "elb": ELBScanner(),
    "ebs": EBSScanner(),
}

__all__ = [
    "BaseScanner",
    "SCANNER_REGISTRY",
    "EC2Scanner",
    "RDSScanner",
    "S3Scanner",
    "ELBScanner",
    "EBSScanner",
    "tags_match",
    "flatten_aws_tags",
]
