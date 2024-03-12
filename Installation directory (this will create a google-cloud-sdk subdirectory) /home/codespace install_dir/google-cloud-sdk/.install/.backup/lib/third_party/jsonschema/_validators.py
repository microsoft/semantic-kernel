import re

from jsonschema import _utils
from jsonschema.exceptions import FormatError, ValidationError
from jsonschema.compat import iteritems


def patternProperties(validator, patternProperties, instance, schema):
    if not validator.is_type(instance, "object"):
        return

    for pattern, subschema in iteritems(patternProperties):
        for k, v in iteritems(instance):
            if re.search(pattern, k):
                for error in validator.descend(
                    v, subschema, path=k, schema_path=pattern,
                ):
                    yield error


def additionalProperties(validator, aP, instance, schema):
    if not validator.is_type(instance, "object"):
        return

    extras = set(_utils.find_additional_properties(instance, schema))

    if validator.is_type(aP, "object"):
        for extra in extras:
            for error in validator.descend(instance[extra], aP, path=extra):
                yield error
    elif not aP and extras:
        if "patternProperties" in schema:
            patterns = sorted(schema["patternProperties"])
            if len(extras) == 1:
                verb = "does"
            else:
                verb = "do"
            error = "%s %s not match any of the regexes: %s" % (
                ", ".join(map(repr, sorted(extras))),
                verb,
                ", ".join(map(repr, patterns)),
            )
            yield ValidationError(error)
        else:
            error = "Additional properties are not allowed (%s %s unexpected)"
            yield ValidationError(error % _utils.extras_msg(extras))


def items(validator, items, instance, schema):
    if not validator.is_type(instance, "array"):
        return

    if validator.is_type(items, "object"):
        for index, item in enumerate(instance):
            for error in validator.descend(item, items, path=index):
                yield error
    else:
        for (index, item), subschema in zip(enumerate(instance), items):
            for error in validator.descend(
                item, subschema, path=index, schema_path=index,
            ):
                yield error


def additionalItems(validator, aI, instance, schema):
    if (
        not validator.is_type(instance, "array") or
        validator.is_type(schema.get("items", {}), "object")
    ):
        return

    len_items = len(schema.get("items", []))
    if validator.is_type(aI, "object"):
        for index, item in enumerate(instance[len_items:], start=len_items):
            for error in validator.descend(item, aI, path=index):
                yield error
    elif not aI and len(instance) > len(schema.get("items", [])):
        error = "Additional items are not allowed (%s %s unexpected)"
        yield ValidationError(
            error %
            _utils.extras_msg(instance[len(schema.get("items", [])):])
        )


def minimum(validator, minimum, instance, schema):
    if not validator.is_type(instance, "number"):
        return

    if schema.get("exclusiveMinimum", False):
        failed = instance <= minimum
        cmp = "less than or equal to"
    else:
        failed = instance < minimum
        cmp = "less than"

    if failed:
        yield ValidationError(
            "%r is %s the minimum of %r" % (instance, cmp, minimum)
        )


def maximum(validator, maximum, instance, schema):
    if not validator.is_type(instance, "number"):
        return

    if schema.get("exclusiveMaximum", False):
        failed = instance >= maximum
        cmp = "greater than or equal to"
    else:
        failed = instance > maximum
        cmp = "greater than"

    if failed:
        yield ValidationError(
            "%r is %s the maximum of %r" % (instance, cmp, maximum)
        )


def multipleOf(validator, dB, instance, schema):
    if not validator.is_type(instance, "number"):
        return

    if isinstance(dB, float):
        quotient = instance / dB
        failed = int(quotient) != quotient
    else:
        failed = instance % dB

    if failed:
        yield ValidationError("%r is not a multiple of %r" % (instance, dB))


def minItems(validator, mI, instance, schema):
    if validator.is_type(instance, "array") and len(instance) < mI:
        yield ValidationError("%r is too short" % (instance,))


def maxItems(validator, mI, instance, schema):
    if validator.is_type(instance, "array") and len(instance) > mI:
        yield ValidationError("%r is too long" % (instance,))


def uniqueItems(validator, uI, instance, schema):
    if (
        uI and
        validator.is_type(instance, "array") and
        not _utils.uniq(instance)
    ):
        yield ValidationError("%r has non-unique elements" % (instance,))


def pattern(validator, patrn, instance, schema):
    if (
        validator.is_type(instance, "string") and
        not re.search(patrn, instance)
    ):
        yield ValidationError("%r does not match %r" % (instance, patrn))


def format(validator, format, instance, schema):
    if validator.format_checker is not None:
        try:
            validator.format_checker.check(instance, format)
        except FormatError as error:
            yield ValidationError(error.message, cause=error.cause)


def minLength(validator, mL, instance, schema):
    if validator.is_type(instance, "string") and len(instance) < mL:
        yield ValidationError("%r is too short" % (instance,))


def maxLength(validator, mL, instance, schema):
    if validator.is_type(instance, "string") and len(instance) > mL:
        yield ValidationError("%r is too long" % (instance,))


def dependencies(validator, dependencies, instance, schema):
    if not validator.is_type(instance, "object"):
        return

    for property, dependency in iteritems(dependencies):
        if property not in instance:
            continue

        if validator.is_type(dependency, "object"):
            for error in validator.descend(
                instance, dependency, schema_path=property,
            ):
                yield error
        else:
            dependencies = _utils.ensure_list(dependency)
            for dependency in dependencies:
                if dependency not in instance:
                    yield ValidationError(
                        "%r is a dependency of %r" % (dependency, property)
                    )


def enum(validator, enums, instance, schema):
    if instance not in enums:
        yield ValidationError("%r is not one of %r" % (instance, enums))


def ref(validator, ref, instance, schema):
    resolve = getattr(validator.resolver, "resolve", None)
    if resolve is None:
        with validator.resolver.resolving(ref) as resolved:
            for error in validator.descend(instance, resolved):
                yield error
    else:
        scope, resolved = validator.resolver.resolve(ref)
        validator.resolver.push_scope(scope)

        try:
            for error in validator.descend(instance, resolved):
                yield error
        finally:
            validator.resolver.pop_scope()


def type_draft3(validator, types, instance, schema):
    types = _utils.ensure_list(types)

    all_errors = []
    for index, type in enumerate(types):
        if type == "any":
            return
        if validator.is_type(type, "object"):
            errors = list(validator.descend(instance, type, schema_path=index))
            if not errors:
                return
            all_errors.extend(errors)
        else:
            if validator.is_type(instance, type):
                return
    else:
        yield ValidationError(
            _utils.types_msg(instance, types), context=all_errors,
        )


def properties_draft3(validator, properties, instance, schema):
    if not validator.is_type(instance, "object"):
        return

    for property, subschema in iteritems(properties):
        if property in instance:
            for error in validator.descend(
                instance[property],
                subschema,
                path=property,
                schema_path=property,
            ):
                yield error
        elif subschema.get("required", False):
            error = ValidationError("%r is a required property" % property)
            error._set(
                validator="required",
                validator_value=subschema["required"],
                instance=instance,
                schema=schema,
            )
            error.path.appendleft(property)
            error.schema_path.extend([property, "required"])
            yield error


def disallow_draft3(validator, disallow, instance, schema):
    for disallowed in _utils.ensure_list(disallow):
        if validator.is_valid(instance, {"type": [disallowed]}):
            yield ValidationError(
                "%r is disallowed for %r" % (disallowed, instance)
            )


def extends_draft3(validator, extends, instance, schema):
    if validator.is_type(extends, "object"):
        for error in validator.descend(instance, extends):
            yield error
        return
    for index, subschema in enumerate(extends):
        for error in validator.descend(instance, subschema, schema_path=index):
            yield error


def type_draft4(validator, types, instance, schema):
    types = _utils.ensure_list(types)

    if not any(validator.is_type(instance, type) for type in types):
        yield ValidationError(_utils.types_msg(instance, types))


def properties_draft4(validator, properties, instance, schema):
    if not validator.is_type(instance, "object"):
        return

    for property, subschema in iteritems(properties):
        if property in instance:
            for error in validator.descend(
                instance[property],
                subschema,
                path=property,
                schema_path=property,
            ):
                yield error


def required_draft4(validator, required, instance, schema):
    if not validator.is_type(instance, "object"):
        return
    for property in required:
        if property not in instance:
            yield ValidationError("%r is a required property" % property)


def minProperties_draft4(validator, mP, instance, schema):
    if validator.is_type(instance, "object") and len(instance) < mP:
        yield ValidationError(
            "%r does not have enough properties" % (instance,)
        )


def maxProperties_draft4(validator, mP, instance, schema):
    if not validator.is_type(instance, "object"):
        return
    if validator.is_type(instance, "object") and len(instance) > mP:
        yield ValidationError("%r has too many properties" % (instance,))


def allOf_draft4(validator, allOf, instance, schema):
    for index, subschema in enumerate(allOf):
        for error in validator.descend(instance, subschema, schema_path=index):
            yield error


def oneOf_draft4(validator, oneOf, instance, schema):
    subschemas = enumerate(oneOf)
    all_errors = []
    for index, subschema in subschemas:
        errs = list(validator.descend(instance, subschema, schema_path=index))
        if not errs:
            first_valid = subschema
            break
        all_errors.extend(errs)
    else:
        yield ValidationError(
            "%r is not valid under any of the given schemas" % (instance,),
            context=all_errors,
        )

    more_valid = [s for i, s in subschemas if validator.is_valid(instance, s)]
    if more_valid:
        more_valid.append(first_valid)
        reprs = ", ".join(repr(schema) for schema in more_valid)
        yield ValidationError(
            "%r is valid under each of %s" % (instance, reprs)
        )


def anyOf_draft4(validator, anyOf, instance, schema):
    all_errors = []
    for index, subschema in enumerate(anyOf):
        errs = list(validator.descend(instance, subschema, schema_path=index))
        if not errs:
            break
        all_errors.extend(errs)
    else:
        yield ValidationError(
            "%r is not valid under any of the given schemas" % (instance,),
            context=all_errors,
        )


def not_draft4(validator, not_schema, instance, schema):
    if validator.is_valid(instance, not_schema):
        yield ValidationError(
            "%r is not allowed for %r" % (not_schema, instance)
        )
