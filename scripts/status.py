from yuan.models import Project, Package


def calculate():
    projects = []

    for name in Project.all():
        for item in Project.list(name):
            item = Project(family=item['family'], name=item['name'])
            packages = Project.sort(item.packages)

            packages = filter(
                lambda o: o['tag'] == 'stable',
                packages.values()
            )

            if not packages:
                continue

            pkg = Package(**packages[0])
            item.dependents = pkg.get('dependents', [])
            projects.append(item)

    def _sort_by_time(item):
        if 'update_at' in item:
            return datetime.strptime(
                item['updated_at'], '%Y-%m-%dT%H:%M:%SZ'
            )
        return None

    popular = sorted(
        projects, key=lambda o: len(o.dependents), reverse=True
    )[:50]

    latest = sorted(
        projects, key=_sort_by_time, reverse=True
    )[:50]
    return {'popular': popular, 'latest': latest}
