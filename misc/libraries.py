import os
import pkg_resources

def calc_container(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

dists = [d for d in pkg_resources.working_set]

total_size = 0
for dist in dists:
    try:
        path = os.path.join(dist.location, dist.project_name)
        size = calc_container(path)
        if size/1000 > 1.0:
            print (f"{dist}: {size/1000} KB")
            print("-"*40)
            total_size += size/1000
    except OSError:
        "{} no longer exists".format(dist.project_name)

print("="*40)
print(f"Total size of all packages: {round(total_size, 2)} KB")