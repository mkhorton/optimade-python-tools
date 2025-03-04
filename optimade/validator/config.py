""" This submodule defines constant values and definitions
from the OPTIMADE specification for use by the validator.

The `VALIDATOR_CONFIG` object can be imported and modified
before calling the validator inside a Python script to customise
the hardcoded values.

"""

from collections.abc import Container
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings

from optimade.models import (
    DataType,
    IndexInfoResponse,
    InfoResponse,
    StructureFeatures,
    SupportLevel,
)
from optimade.server.mappers import BaseResourceMapper
from optimade.server.schemas import ENTRY_INFO_SCHEMAS, retrieve_queryable_properties
from optimade.validator.utils import (
    ValidatorLinksResponse,
    ValidatorReferenceResponseMany,
    ValidatorReferenceResponseOne,
    ValidatorStructureResponseMany,
    ValidatorStructureResponseOne,
)

__all__ = ("ValidatorConfig", "VALIDATOR_CONFIG")

_ENTRY_SCHEMAS = {
    endp: retrieve_queryable_properties(
        ENTRY_INFO_SCHEMAS[endp], ("id", "type", "attributes")
    )
    for endp in ENTRY_INFO_SCHEMAS
}

_ENTRY_ENDPOINTS = ("structures", "references", "calculations")

_NON_ENTRY_ENDPOINTS = ("info", "links", "versions")


_RESPONSE_CLASSES = {
    "references": ValidatorReferenceResponseMany,
    "references/": ValidatorReferenceResponseOne,
    "structures": ValidatorStructureResponseMany,
    "structures/": ValidatorStructureResponseOne,
    "info": InfoResponse,
    "links": ValidatorLinksResponse,
}

_RESPONSE_CLASSES_INDEX = {
    "info": IndexInfoResponse,
    "links": ValidatorLinksResponse,
}

_ENUM_DUMMY_VALUES = {
    "structures": {
        "structure_features": [allowed.value for allowed in StructureFeatures]
    }
}


_UNIQUE_PROPERTIES = ("id", "immutable_id")

inclusive_ops = ("=", "<=", ">=")
substring_operators = ("CONTAINS", "STARTS WITH", "STARTS", "ENDS WITH", "ENDS")

_INCLUSIVE_OPERATORS = {
    DataType.STRING: inclusive_ops + substring_operators,
    # N.B. "=" and "<=" are disabled due to issue with microseconds stored in database vs API response (see Materials-Consortia/optimade-python-tools/#606)
    # ">=" is fine as all microsecond trimming will round times down
    DataType.TIMESTAMP: (
        # "=",
        # "<=",
        ">=",
    ),
    DataType.INTEGER: inclusive_ops,
    DataType.FLOAT: (),
    DataType.LIST: ("HAS", "HAS ALL", "HAS ANY", "LENGTH"),
}

exclusive_ops = ("!=", "<", ">")

_EXCLUSIVE_OPERATORS = {
    DataType.STRING: exclusive_ops,
    DataType.TIMESTAMP: (),
    DataType.FLOAT: (),
    DataType.INTEGER: exclusive_ops,
    DataType.LIST: (),
}


_FIELD_SPECIFIC_OVERRIDES = {
    "chemical_formula_anonymous": {
        SupportLevel.OPTIONAL: substring_operators,
    },
    "chemical_formula_reduced": {
        SupportLevel.OPTIONAL: substring_operators,
    },
    # Only check immutable_ids can be queried for equality
    "immutable_id": {
        SupportLevel.OPTIONAL: [
            op
            for op in substring_operators + inclusive_ops + exclusive_ops
            if op != "="
        ],
    },
    "structure_features": {
        SupportLevel.OPTIONAL: "LENGTH",
    },
}


class ValidatorConfig(BaseSettings):
    """This class stores validator config parameters in a way that
    can be easily modified for testing niche implementations. Many
    of these fields are determined by the specification directly,
    but it may be desirable to modify them in certain cases.

    """

    response_classes: dict[str, Any] = Field(
        _RESPONSE_CLASSES,
        description="Dictionary containing the mapping between endpoints and response classes for the main database",
    )

    response_classes_index: dict[str, Any] = Field(
        _RESPONSE_CLASSES_INDEX,
        description="Dictionary containing the mapping between endpoints and response classes for the index meta-database",
    )

    entry_schemas: dict[str, Any] = Field(
        _ENTRY_SCHEMAS, description="The entry listing endpoint schemas"
    )

    entry_endpoints: set[str] = Field(
        _ENTRY_ENDPOINTS,
        description="The entry endpoints to validate, if present in the API's `/info` response `entry_types_by_format['json']`",
    )

    unique_properties: set[str] = Field(
        _UNIQUE_PROPERTIES,
        description=(
            "Fields that should be treated as unique indexes for all endpoints, "
            "i.e. fields on which filters should return at most one entry."
        ),
    )

    inclusive_operators: dict[DataType, set[str]] = Field(
        _INCLUSIVE_OPERATORS,
        description=(
            "Dictionary mapping OPTIMADE `DataType`s to a list of operators that are 'inclusive', "
            "i.e. those that should return entries with the matching value from the filter."
        ),
    )

    exclusive_operators: dict[DataType, set[str]] = Field(
        _EXCLUSIVE_OPERATORS,
        description=(
            "Dictionary mapping OPTIMADE `DataType`s to a list of operators that are 'exclusive', "
            "i.e. those that should not return entries with the matching value from the filter."
        ),
    )

    field_specific_overrides: dict[str, dict[SupportLevel, Container[str]]] = Field(
        _FIELD_SPECIFIC_OVERRIDES,
        description=(
            "Some fields do not require all type comparison operators to be supported. "
            "This dictionary allows overriding the list of supported operators for a field, using "
            "the field name as a key, and the support level of different operators with a subkey. "
            "Queries on fields listed in this way will pass the validator provided the server returns a 501 status."
        ),
    )

    links_endpoint: str = Field("links", description="The name of the links endpoint")
    versions_endpoint: str = Field(
        "versions", description="The name of the versions endpoint"
    )

    info_endpoint: str = Field("info", description="The name of the info endpoint")
    non_entry_endpoints: set[str] = Field(
        _NON_ENTRY_ENDPOINTS,
        description="The list specification-mandated endpoint names that do not contain entries",
    )
    top_level_non_attribute_fields: set[str] = Field(
        BaseResourceMapper.TOP_LEVEL_NON_ATTRIBUTES_FIELDS,
        description="Field names to treat as top-level",
    )

    enum_fallback_values: dict[str, dict[str, list[str]]] = Field(
        _ENUM_DUMMY_VALUES,
        description="Provide fallback values for enum fields to use when validating filters.",
    )


VALIDATOR_CONFIG = ValidatorConfig()
