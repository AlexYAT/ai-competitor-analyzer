"""Enumerations used across schemas and services."""

from enum import StrEnum


class SiteType(StrEnum):
    landing = "landing"
    multi_page_service_site = "multi_page_service_site"
    personal_brand_site = "personal_brand_site"
    blog = "blog"
    directory = "directory"
    marketplace = "marketplace"
    social_page = "social_page"
    irrelevant = "irrelevant"
