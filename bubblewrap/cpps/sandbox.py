import triangulations
import dcel

mD1,t1,b1 = triangulations.cylinder(5,5)
t1stop = t1.boundary_forward(1)
dcel.glue_boundary(mD1,t1,b1,t1stop)

mD2,t2,b2 = triangulations.cylinder(5,5)
t2stop = t2.boundary_forward(1)
dcel.glue_boundary(mD2,t2,b2,t2stop)

dcel.reverse_orientation(mD2)
mD = mD1 | mD2
dcel.glue_boundary(mD,t1stop,t2stop)


print(dcel.oriented_manifold_type(mD))


# speed test simulator
import random
# Params:
# d_objs = [1024*50, 1024*300, 1024*500, 1024*1024]
# about every 1500 secs
#
# 3Mb/s: min speed avg 65KB/sec with 5-10 simultaneous connections
# 6Mb/s: min speed avg 256KB/sec with 3-6 simultaneous connections
# 12Mb/s: min speed avg 512KB/sec with 2-5 simultaneous connections


time = 60*60*12
speed = 3 * 1024 / 8
d_objs = [1024*25, 1024*50, 1024*200, 1024*1024]

min_speed = speed
max_connections = 0
total_conn = 0
total_downloaded = 0

current_downloads = []

for t in range(time):
    if random.randint(0,1000) == 0:
        some_num = d_objs[random.randint(0,3)]
        current_downloads.append(some_num)
        total_conn += 1
        total_downloaded += some_num

    per_speed = speed * 1 / len(current_downloads) if len(current_downloads) != 0 else speed
    if per_speed < min_speed:
        min_speed = per_speed

    if len(current_downloads) > max_connections:
        max_connections = len(current_downloads)

    for i in range(len(current_downloads)):
        current_downloads[i] -= per_speed
        if current_downloads[i] < 0:
            current_downloads.pop(i)
            break

print("\n\n")
print("Min speed: %d KB/sec" % (min_speed))
print("Max simultaneous connections: %d" % max_connections)
print("Total connections: %d" % total_conn)
print("Total downloaded: %d GB" % (total_downloaded/1024.0/1024))
