from ..models import Package


def calculate_dependents(pkg, operation):
    dependencies = pkg.get('dependencies', None)
    if not dependencies:
        return

    if isinstance(pkg, Package):
        p = str(pkg)
    else:
        p = '%s/%s@%s' % (pkg['family'], pkg['name'], pkg['version'])

    for dep in dependencies:
        package = _parse(dep)
        if not package:
            continue

        package = Package(**package)
        dependents = package.get('dependents', [])

        if operation == 'delete' and p in dependents:
            dependents.remove(p)
            package.dependents = dependents
            package.save()
            continue

        if operation != 'delete' and p not in dependents:
            dependents.append(p)
            package.dependents = dependents
            package.save()
            continue


def _parse(dep):
    # family/name@version
    if '@' not in dep or '/' not in dep:
        return None

    value, version = dep.split('@')
    family, name = value.split('/')
    return {'family': family, 'name': name, 'version': version}
