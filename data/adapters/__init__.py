"""B03 adapters. All inputs are local; AWS adapters are fixture-only interfaces."""

from data.adapters.base import LocalAdapter


class SyntheticAdapter(LocalAdapter):
    profile = "synthetic"


class PublicDatasetAdapter(LocalAdapter):
    profile = "public"


class Cur2Adapter(LocalAdapter):
    profile = "aws_cur"


class OpenCostAdapter(LocalAdapter):
    profile = "opencost"


class AwsInventoryAdapter(LocalAdapter):
    profile = "aws_boto3"
