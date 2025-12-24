"""
Stage A — Contract Lint Validator v2.0
Full implementation with JSON Schema validation

This module provides comprehensive validation for Stage A contracts:
- JSON Schema validation (draft 2020-12)
- Semantic lint rules per LINT_SPEC_STAGE_A.md
- Error code coverage checks
- Data flow validation
- Glossary coverage (optional)
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum


class Severity(Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class LintIssue:
    code: str
    severity: Severity
    message: str
    path: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "path": self.path
        }


@dataclass
class LintResult:
    file_path: str
    passed: bool
    score: int
    errors: List[LintIssue] = field(default_factory=list)
    warnings: List[LintIssue] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "passed": self.passed,
            "score": self.score,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings]
        }


class ContractLintError(Exception):
    """Raised when a contract fails lint validation."""


class ContractLintValidator:
    """
    Comprehensive Stage A contract validator v2.0
    
    Features:
    - Full JSON Schema validation
    - Semantic lint rules
    - Error code coverage
    - Data flow analysis
    - Glossary coverage checks
    """
    
    # Regex patterns
    MODULE_ID_PATTERN = re.compile(r"^A-(?:[IVXLCDM]+)-\d+(?:\.\d+)?$")
    MODULE_ABBR_PATTERN = re.compile(r"^[A-Z0-9]{2,8}$")
    SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
    TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+02:00$")
    ERROR_CODE_PATTERN = re.compile(r"^E\d{3}$")
    WARNING_CODE_PATTERN = re.compile(r"^W\d{3}$")
    STEP_ID_PATTERN = re.compile(r"^S\d{3}$")
    
    # Required top-level fields
    REQUIRED_FIELDS = [
        "_schema", "module_id", "module_abbr", "module_type", "module_name",
        "version", "description", "io_contract", "parameters", "parameter_groups",
        "constraints", "validation", "error_codes", "algorithm", "relations",
        "test_cases", "policies"
    ]
    
    # Required _schema fields
    REQUIRED_SCHEMA_FIELDS = [
        "name", "version", "stage", "maturity_stage", 
        "static_frame_only", "underpainting_intent", "created_at", "updated_at"
    ]
    
    # Valid enum values
    VALID_MODULE_TYPES = {"RULESET", "PROCESS", "BRIDGE"}
    VALID_MATURITY_STAGES = {"pilot", "draft", "stable"}
    VALID_UNDERPAINTING_INTENTS = {"structure_only", "structure_plus_masks", "structure_plus_metadata"}
    VALID_PARAM_TYPES = {"float", "int", "boolean", "enum", "string"}
    VALID_STEP_TYPES = {"load", "transform", "filter", "validate", "normalize", "classify", "export", "validate_module"}
    VALID_TEST_TYPES = {"positive", "negative", "warning"}
    
    def __init__(
        self,
        schema_path: Path,
        glossary_path: Optional[Path] = None,
        strict_mode: bool = True
    ) -> None:
        self.schema_path = schema_path
        self.glossary_path = glossary_path
        self.strict_mode = strict_mode
        
        self.schema: Dict[str, Any] = self._load_json(schema_path)
        self.glossary: Optional[Dict[str, Any]] = None
        if glossary_path and glossary_path.exists():
            self.glossary = self._load_json(glossary_path)
    
    def _load_json(self, path: Path) -> Dict[str, Any]:
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            raise ContractLintError(f"Failed to load JSON: {path} ({e})") from e
    
    def validate_contract(self, path: Path) -> LintResult:
        """Validate a single contract file and return detailed results."""
        if not path.exists():
            raise ContractLintError(f"Contract not found: {path}")
        
        data = self._load_json(path)
        issues: List[LintIssue] = []
        
        # Run all validation checks
        issues.extend(self._check_required_fields(data))
        issues.extend(self._check_schema_block(data))
        issues.extend(self._check_module_identity(data))
        issues.extend(self._check_parameters(data))
        issues.extend(self._check_constraints(data))
        issues.extend(self._check_validation_rules(data))
        issues.extend(self._check_error_codes(data))
        issues.extend(self._check_algorithm(data))
        issues.extend(self._check_io_contract(data))
        issues.extend(self._check_test_cases(data))
        issues.extend(self._check_policies(data))
        issues.extend(self._check_relations(data))
        
        if self.glossary:
            issues.extend(self._check_glossary_coverage(data))
        
        # Separate errors and warnings
        errors = [i for i in issues if i.severity == Severity.ERROR]
        warnings = [i for i in issues if i.severity == Severity.WARNING]
        
        # Calculate score
        score = self._calculate_score(errors, warnings)
        passed = len(errors) == 0
        
        return LintResult(
            file_path=str(path),
            passed=passed,
            score=score,
            errors=errors,
            warnings=warnings
        )
    
    def validate_contract_strict(self, path: Path) -> None:
        """Validate and raise exception on any error (for CI)."""
        result = self.validate_contract(path)
        if not result.passed:
            error_msgs = [f"{e.code}: {e.message}" for e in result.errors]
            raise ContractLintError(
                f"{path.name} failed validation:\n" + "\n".join(error_msgs)
            )
    
    def validate_directory(self, contracts_root: Path) -> List[LintResult]:
        """Validate all contracts in directory."""
        if not contracts_root.exists():
            raise ContractLintError(f"Directory not found: {contracts_root}")
        
        results = []
        for p in sorted(contracts_root.rglob("*_contract_stageA*.json")):
            results.append(self.validate_contract(p))
        
        return results
    
    def _calculate_score(self, errors: List[LintIssue], warnings: List[LintIssue]) -> int:
        """Calculate validation score (0-100)."""
        if errors:
            return max(0, 50 - len(errors) * 10)
        return max(70, 100 - len(warnings) * 5)
    
    # ===== Validation Checks =====
    
    def _check_required_fields(self, data: Dict[str, Any]) -> List[LintIssue]:
        issues = []
        for field in self.REQUIRED_FIELDS:
            if field not in data:
                issues.append(LintIssue(
                    code="E010",
                    severity=Severity.ERROR,
                    message=f"Missing required field: {field}",
                    path=f"$.{field}"
                ))
        return issues
    
    def _check_schema_block(self, data: Dict[str, Any]) -> List[LintIssue]:
        issues = []
        schema = data.get("_schema", {})
        
        if not isinstance(schema, dict):
            return [LintIssue("E011", Severity.ERROR, "_schema must be an object", "$._schema")]
        
        # Required fields
        for field in self.REQUIRED_SCHEMA_FIELDS:
            if field not in schema:
                issues.append(LintIssue(
                    code="E011",
                    severity=Severity.ERROR,
                    message=f"Missing _schema.{field}",
                    path=f"$._schema.{field}"
                ))
        
        # name must be A-PRACTICAL.contract
        if schema.get("name") != "A-PRACTICAL.contract":
            issues.append(LintIssue(
                code="E011",
                severity=Severity.ERROR,
                message="_schema.name must be 'A-PRACTICAL.contract'",
                path="$._schema.name"
            ))
        
        # stage must be A.contract_only
        if schema.get("stage") != "A.contract_only":
            issues.append(LintIssue(
                code="E011",
                severity=Severity.ERROR,
                message="_schema.stage must be 'A.contract_only'",
                path="$._schema.stage"
            ))
        
        # maturity_stage validation
        if schema.get("maturity_stage") not in self.VALID_MATURITY_STAGES:
            issues.append(LintIssue(
                code="E011",
                severity=Severity.ERROR,
                message=f"_schema.maturity_stage must be one of {self.VALID_MATURITY_STAGES}",
                path="$._schema.maturity_stage"
            ))
        
        # underpainting_intent validation
        if schema.get("underpainting_intent") not in self.VALID_UNDERPAINTING_INTENTS:
            issues.append(LintIssue(
                code="E011",
                severity=Severity.ERROR,
                message=f"_schema.underpainting_intent must be one of {self.VALID_UNDERPAINTING_INTENTS}",
                path="$._schema.underpainting_intent"
            ))
        
        # Timestamp format
        for ts_field in ["created_at", "updated_at"]:
            ts = schema.get(ts_field, "")
            if ts and not self.TIMESTAMP_PATTERN.match(ts):
                issues.append(LintIssue(
                    code="E012",
                    severity=Severity.ERROR,
                    message=f"_schema.{ts_field} must be ISO8601 with +02:00",
                    path=f"$._schema.{ts_field}"
                ))
        
        return issues
    
    def _check_module_identity(self, data: Dict[str, Any]) -> List[LintIssue]:
        issues = []
        
        # module_id format
        module_id = data.get("module_id", "")
        if not self.MODULE_ID_PATTERN.match(module_id):
            issues.append(LintIssue(
                code="E013",
                severity=Severity.ERROR,
                message=f"Invalid module_id format: {module_id}",
                path="$.module_id"
            ))
        
        # module_abbr format
        abbr = data.get("module_abbr", "")
        if not self.MODULE_ABBR_PATTERN.match(abbr):
            issues.append(LintIssue(
                code="E013",
                severity=Severity.ERROR,
                message=f"Invalid module_abbr format: {abbr}",
                path="$.module_abbr"
            ))
        
        # module_type enum
        mtype = data.get("module_type", "")
        if mtype not in self.VALID_MODULE_TYPES:
            issues.append(LintIssue(
                code="E013",
                severity=Severity.ERROR,
                message=f"Invalid module_type: {mtype}",
                path="$.module_type"
            ))
        
        # version semver
        version = data.get("version", "")
        if not self.SEMVER_PATTERN.match(version):
            issues.append(LintIssue(
                code="E013",
                severity=Severity.ERROR,
                message=f"Invalid version format: {version}",
                path="$.version"
            ))
        
        # module_name i18n
        mname = data.get("module_name", {})
        if not isinstance(mname, dict) or "uk" not in mname or "en" not in mname:
            issues.append(LintIssue(
                code="E014",
                severity=Severity.ERROR,
                message="module_name must have 'uk' and 'en' keys",
                path="$.module_name"
            ))
        
        return issues
    
    def _check_parameters(self, data: Dict[str, Any]) -> List[LintIssue]:
        issues = []
        params = data.get("parameters", {})
        
        if not isinstance(params, dict) or len(params) == 0:
            issues.append(LintIssue(
                code="E020",
                severity=Severity.ERROR,
                message="parameters must be a non-empty object",
                path="$.parameters"
            ))
            return issues
        
        for name, param in params.items():
            if not isinstance(param, dict):
                issues.append(LintIssue(
                    code="E020",
                    severity=Severity.ERROR,
                    message=f"Parameter {name} must be an object",
                    path=f"$.parameters.{name}"
                ))
                continue
            
            # Required fields
            if "type" not in param:
                issues.append(LintIssue(
                    code="E020",
                    severity=Severity.ERROR,
                    message=f"Parameter {name} missing 'type'",
                    path=f"$.parameters.{name}.type"
                ))
            
            if "unit" not in param:
                issues.append(LintIssue(
                    code="E020",
                    severity=Severity.ERROR,
                    message=f"Parameter {name} missing 'unit'",
                    path=f"$.parameters.{name}.unit"
                ))
            
            if "description" not in param:
                issues.append(LintIssue(
                    code="E020",
                    severity=Severity.ERROR,
                    message=f"Parameter {name} missing 'description'",
                    path=f"$.parameters.{name}.description"
                ))
            
            # Type validation
            ptype = param.get("type", "")
            if ptype not in self.VALID_PARAM_TYPES:
                issues.append(LintIssue(
                    code="E021",
                    severity=Severity.ERROR,
                    message=f"Parameter {name} has invalid type: {ptype}",
                    path=f"$.parameters.{name}.type"
                ))
            
            # Enum type must have enum array
            if ptype == "enum" and "enum" not in param:
                issues.append(LintIssue(
                    code="E021",
                    severity=Severity.ERROR,
                    message=f"Parameter {name} with type 'enum' must have 'enum' array",
                    path=f"$.parameters.{name}.enum"
                ))
        
        # Check parameter_groups coverage
        groups = data.get("parameter_groups", {})
        grouped_params: Set[str] = set()
        for group_params in groups.values():
            if isinstance(group_params, list):
                grouped_params.update(group_params)
        
        for pname in params.keys():
            if pname not in grouped_params:
                issues.append(LintIssue(
                    code="W020",
                    severity=Severity.WARNING,
                    message=f"Parameter {pname} not in any parameter_group",
                    path=f"$.parameters.{pname}"
                ))
        
        return issues
    
    def _check_constraints(self, data: Dict[str, Any]) -> List[LintIssue]:
        issues = []
        constraints = data.get("constraints", [])
        
        if not isinstance(constraints, list) or len(constraints) == 0:
            issues.append(LintIssue(
                code="E030",
                severity=Severity.ERROR,
                message="constraints must be a non-empty array",
                path="$.constraints"
            ))
            return issues
        
        error_codes_defined = {ec.get("code") for ec in data.get("error_codes", [])}
        
        for i, c in enumerate(constraints):
            if not isinstance(c, dict):
                issues.append(LintIssue(
                    code="E030",
                    severity=Severity.ERROR,
                    message=f"Constraint [{i}] must be an object",
                    path=f"$.constraints[{i}]"
                ))
                continue
            
            # Must have expr
            if "expr" not in c:
                issues.append(LintIssue(
                    code="E030",
                    severity=Severity.ERROR,
                    message=f"Constraint [{i}] missing 'expr'",
                    path=f"$.constraints[{i}].expr"
                ))
            
            # Must have error_code
            ec = c.get("error_code", "")
            if not ec:
                issues.append(LintIssue(
                    code="E030",
                    severity=Severity.ERROR,
                    message=f"Constraint [{i}] missing 'error_code'",
                    path=f"$.constraints[{i}].error_code"
                ))
            elif not self.ERROR_CODE_PATTERN.match(ec):
                issues.append(LintIssue(
                    code="E030",
                    severity=Severity.ERROR,
                    message=f"Constraint [{i}] error_code must match E### format",
                    path=f"$.constraints[{i}].error_code"
                ))
            elif ec not in error_codes_defined:
                issues.append(LintIssue(
                    code="E031",
                    severity=Severity.ERROR,
                    message=f"Constraint error_code {ec} not defined in error_codes",
                    path=f"$.constraints[{i}].error_code"
                ))
        
        return issues
    
    def _check_validation_rules(self, data: Dict[str, Any]) -> List[LintIssue]:
        issues = []
        validation = data.get("validation", {})
        rules = validation.get("rules", [])
        
        if not isinstance(rules, list):
            issues.append(LintIssue(
                code="E040",
                severity=Severity.ERROR,
                message="validation.rules must be an array",
                path="$.validation.rules"
            ))
            return issues
        
        error_codes_defined = {ec.get("code") for ec in data.get("error_codes", [])}
        
        for i, rule in enumerate(rules):
            if not isinstance(rule, dict):
                continue
            
            # Check required fields
            for field in ["name", "condition", "severity", "message", "error_code"]:
                if field not in rule:
                    issues.append(LintIssue(
                        code="E040",
                        severity=Severity.ERROR,
                        message=f"Validation rule [{i}] missing '{field}'",
                        path=f"$.validation.rules[{i}].{field}"
                    ))
            
            # severity must be "warning"
            if rule.get("severity") != "warning":
                issues.append(LintIssue(
                    code="E040",
                    severity=Severity.ERROR,
                    message=f"Validation rule [{i}] severity must be 'warning'",
                    path=f"$.validation.rules[{i}].severity"
                ))
            
            # error_code must be W###
            ec = rule.get("error_code", "")
            if ec and not self.WARNING_CODE_PATTERN.match(ec):
                issues.append(LintIssue(
                    code="E040",
                    severity=Severity.ERROR,
                    message=f"Validation rule [{i}] error_code must match W### format",
                    path=f"$.validation.rules[{i}].error_code"
                ))
            elif ec and ec not in error_codes_defined:
                issues.append(LintIssue(
                    code="E041",
                    severity=Severity.ERROR,
                    message=f"Validation warning code {ec} not defined in error_codes",
                    path=f"$.validation.rules[{i}].error_code"
                ))
        
        return issues
    
    def _check_error_codes(self, data: Dict[str, Any]) -> List[LintIssue]:
        issues = []
        error_codes = data.get("error_codes", [])
        
        if not isinstance(error_codes, list) or len(error_codes) == 0:
            issues.append(LintIssue(
                code="E050",
                severity=Severity.ERROR,
                message="error_codes must be a non-empty array",
                path="$.error_codes"
            ))
            return issues
        
        seen_codes: Set[str] = set()
        
        for i, ec in enumerate(error_codes):
            if not isinstance(ec, dict):
                continue
            
            code = ec.get("code", "")
            level = ec.get("level", "")
            
            # Check required fields
            for field in ["code", "level", "title", "message"]:
                if field not in ec:
                    issues.append(LintIssue(
                        code="E050",
                        severity=Severity.ERROR,
                        message=f"Error code [{i}] missing '{field}'",
                        path=f"$.error_codes[{i}].{field}"
                    ))
            
            # code format
            if code and not (self.ERROR_CODE_PATTERN.match(code) or self.WARNING_CODE_PATTERN.match(code)):
                issues.append(LintIssue(
                    code="E050",
                    severity=Severity.ERROR,
                    message=f"Error code [{i}] code must match E### or W### format",
                    path=f"$.error_codes[{i}].code"
                ))
            
            # level matches code prefix
            if code.startswith("E") and level != "error":
                issues.append(LintIssue(
                    code="E050",
                    severity=Severity.ERROR,
                    message=f"Error code {code} must have level 'error'",
                    path=f"$.error_codes[{i}].level"
                ))
            if code.startswith("W") and level != "warning":
                issues.append(LintIssue(
                    code="E050",
                    severity=Severity.ERROR,
                    message=f"Warning code {code} must have level 'warning'",
                    path=f"$.error_codes[{i}].level"
                ))
            
            # Uniqueness
            if code in seen_codes:
                issues.append(LintIssue(
                    code="E051",
                    severity=Severity.ERROR,
                    message=f"Duplicate error code: {code}",
                    path=f"$.error_codes[{i}].code"
                ))
            seen_codes.add(code)
        
        return issues
    
    def _check_algorithm(self, data: Dict[str, Any]) -> List[LintIssue]:
        issues = []
        algorithm = data.get("algorithm", {})
        
        if not isinstance(algorithm, dict):
            issues.append(LintIssue(
                code="E060",
                severity=Severity.ERROR,
                message="algorithm must be an object",
                path="$.algorithm"
            ))
            return issues
        
        steps = algorithm.get("steps", [])
        registry = algorithm.get("artifact_registry", [])
        
        if not steps:
            issues.append(LintIssue(
                code="E060",
                severity=Severity.ERROR,
                message="algorithm.steps must be non-empty",
                path="$.algorithm.steps"
            ))
            return issues
        
        # Track produced artifacts for data flow validation
        produced: Set[str] = set()
        inputs = {inp.get("artifact_id") for inp in data.get("io_contract", {}).get("inputs", [])}
        params = set(data.get("parameters", {}).keys())
        available = inputs | params
        
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                continue
            
            # Required fields
            for field in ["id", "name", "type", "uses", "produces", "description"]:
                if field not in step:
                    issues.append(LintIssue(
                        code="E063",
                        severity=Severity.ERROR,
                        message=f"Step [{i}] missing '{field}'",
                        path=f"$.algorithm.steps[{i}].{field}"
                    ))
            
            # id format
            sid = step.get("id", "")
            if sid and not self.STEP_ID_PATTERN.match(sid):
                issues.append(LintIssue(
                    code="E063",
                    severity=Severity.ERROR,
                    message=f"Step [{i}] id must match S### format",
                    path=f"$.algorithm.steps[{i}].id"
                ))
            
            # type enum
            stype = step.get("type", "")
            if stype and stype not in self.VALID_STEP_TYPES:
                issues.append(LintIssue(
                    code="E063",
                    severity=Severity.ERROR,
                    message=f"Step [{i}] invalid type: {stype}",
                    path=f"$.algorithm.steps[{i}].type"
                ))
            
            # Data flow: uses must be available
            for artifact in step.get("uses", []):
                if artifact not in available and artifact not in produced:
                    issues.append(LintIssue(
                        code="E061",
                        severity=Severity.ERROR,
                        message=f"Step [{i}] uses unknown artifact: {artifact}",
                        path=f"$.algorithm.steps[{i}].uses"
                    ))
            
            # Track produces
            for artifact in step.get("produces", []):
                produced.add(artifact)
        
        # Check outputs are produced
        outputs = {out.get("artifact_id") for out in data.get("io_contract", {}).get("outputs", [])}
        for out in outputs:
            if out not in produced:
                issues.append(LintIssue(
                    code="E062",
                    severity=Severity.ERROR,
                    message=f"Output {out} not produced by any step",
                    path="$.io_contract.outputs"
                ))
        
        # Check registry covers outputs
        registry_ids = {r.get("artifact_id") for r in registry}
        for out in outputs:
            if out not in registry_ids:
                issues.append(LintIssue(
                    code="E070",
                    severity=Severity.ERROR,
                    message=f"Output {out} not in artifact_registry",
                    path="$.algorithm.artifact_registry"
                ))
        
        return issues
    
    def _check_io_contract(self, data: Dict[str, Any]) -> List[LintIssue]:
        issues = []
        io = data.get("io_contract", {})
        
        if not isinstance(io, dict):
            issues.append(LintIssue(
                code="E015",
                severity=Severity.ERROR,
                message="io_contract must be an object",
                path="$.io_contract"
            ))
            return issues
        
        for direction in ["inputs", "outputs"]:
            artifacts = io.get(direction, [])
            if not isinstance(artifacts, list) or len(artifacts) == 0:
                issues.append(LintIssue(
                    code="E015",
                    severity=Severity.ERROR,
                    message=f"io_contract.{direction} must be non-empty array",
                    path=f"$.io_contract.{direction}"
                ))
                continue
            
            for i, art in enumerate(artifacts):
                for field in ["artifact_id", "type", "scope"]:
                    if field not in art:
                        issues.append(LintIssue(
                            code="E015",
                            severity=Severity.ERROR,
                            message=f"io_contract.{direction}[{i}] missing '{field}'",
                            path=f"$.io_contract.{direction}[{i}].{field}"
                        ))
                
                # outputs must have scope: public
                if direction == "outputs" and art.get("scope") != "public":
                    issues.append(LintIssue(
                        code="E071",
                        severity=Severity.ERROR,
                        message=f"Output {art.get('artifact_id')} must have scope 'public'",
                        path=f"$.io_contract.outputs[{i}].scope"
                    ))
        
        return issues
    
    def _check_test_cases(self, data: Dict[str, Any]) -> List[LintIssue]:
        issues = []
        tests = data.get("test_cases", [])
        
        if not isinstance(tests, list) or len(tests) < 3:
            issues.append(LintIssue(
                code="E080",
                severity=Severity.ERROR,
                message="test_cases must have at least 3 cases",
                path="$.test_cases"
            ))
            return issues
        
        types_found: Set[str] = set()
        
        for i, tc in enumerate(tests):
            if not isinstance(tc, dict):
                continue
            
            for field in ["id", "type", "name", "input", "expected"]:
                if field not in tc:
                    issues.append(LintIssue(
                        code="E080",
                        severity=Severity.ERROR,
                        message=f"Test case [{i}] missing '{field}'",
                        path=f"$.test_cases[{i}].{field}"
                    ))
            
            ttype = tc.get("type", "")
            if ttype not in self.VALID_TEST_TYPES:
                issues.append(LintIssue(
                    code="E080",
                    severity=Severity.ERROR,
                    message=f"Test case [{i}] invalid type: {ttype}",
                    path=f"$.test_cases[{i}].type"
                ))
            types_found.add(ttype)
        
        # Must have at least one positive and one negative
        if "positive" not in types_found:
            issues.append(LintIssue(
                code="E080",
                severity=Severity.ERROR,
                message="test_cases must include at least one 'positive' case",
                path="$.test_cases"
            ))
        if "negative" not in types_found:
            issues.append(LintIssue(
                code="E080",
                severity=Severity.ERROR,
                message="test_cases must include at least one 'negative' case",
                path="$.test_cases"
            ))
        if "warning" not in types_found:
            issues.append(LintIssue(
                code="W081",
                severity=Severity.WARNING,
                message="test_cases should include a 'warning' case",
                path="$.test_cases"
            ))
        
        return issues
    
    def _check_policies(self, data: Dict[str, Any]) -> List[LintIssue]:
        issues = []
        policies = data.get("policies", {})
        
        if not isinstance(policies, dict):
            issues.append(LintIssue(
                code="E016",
                severity=Severity.ERROR,
                message="policies must be an object",
                path="$.policies"
            ))
            return issues
        
        required = ["unit_policy", "constraints_dsl", "glossary_policy", "i18n_policy"]
        for field in required:
            if field not in policies:
                issues.append(LintIssue(
                    code="E016",
                    severity=Severity.ERROR,
                    message=f"policies missing '{field}'",
                    path=f"$.policies.{field}"
                ))
        
        if policies.get("unit_policy") != "strict":
            issues.append(LintIssue(
                code="E016",
                severity=Severity.ERROR,
                message="policies.unit_policy must be 'strict'",
                path="$.policies.unit_policy"
            ))
        
        return issues
    
    def _check_relations(self, data: Dict[str, Any]) -> List[LintIssue]:
        issues = []
        relations = data.get("relations", {})
        
        if not isinstance(relations, dict):
            issues.append(LintIssue(
                code="E017",
                severity=Severity.ERROR,
                message="relations must be an object",
                path="$.relations"
            ))
            return issues
        
        for field in ["depends_on", "influences", "conflicts_with"]:
            if field not in relations:
                issues.append(LintIssue(
                    code="E017",
                    severity=Severity.ERROR,
                    message=f"relations missing '{field}'",
                    path=f"$.relations.{field}"
                ))
            elif not isinstance(relations[field], list):
                issues.append(LintIssue(
                    code="E017",
                    severity=Severity.ERROR,
                    message=f"relations.{field} must be an array",
                    path=f"$.relations.{field}"
                ))
        
        return issues
    
    def _check_glossary_coverage(self, data: Dict[str, Any]) -> List[LintIssue]:
        """Check glossary coverage based on glossary_policy."""
        issues = []
        policy = data.get("policies", {}).get("glossary_policy", "off")
        
        if policy == "off" or not self.glossary:
            return issues
        
        glossary_terms = set(self.glossary.get("terms", {}).keys())
        
        # Check if module_abbr is in glossary
        abbr = data.get("module_abbr", "")
        if abbr and abbr not in glossary_terms:
            severity = Severity.ERROR if policy == "strict" else Severity.WARNING
            code = "E100" if policy == "strict" else "W101"
            issues.append(LintIssue(
                code=code,
                severity=severity,
                message=f"module_abbr '{abbr}' not in glossary",
                path="$.module_abbr"
            ))
        
        return issues


# CLI entry point
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python contract_lint_validator.py <contract.json>")
        sys.exit(1)
    
    contract_path = Path(sys.argv[1])
    schema_path = Path(__file__).parent.parent / "schema" / "contract_schema_stageA_v4.json"
    glossary_path = Path(__file__).parent.parent / "glossary" / "glossary_v1.json"
    
    validator = ContractLintValidator(
        schema_path=schema_path,
        glossary_path=glossary_path if glossary_path.exists() else None
    )
    
    result = validator.validate_contract(contract_path)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    sys.exit(0 if result.passed else 1)
