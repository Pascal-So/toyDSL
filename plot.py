import matplotlib.pyplot as plt
import argparse
import numpy as np

font = "Ubuntu"
symbols = ["D","o","s","+"]
colors = ["#618DF5","#F5618D","#6BF561","#F5A161","#A161F5","#494949"]
background = "#e7e4e4"

ax2 = plt.axes()
ax2.set_facecolor(background)

inpute_sizes=[16,32,64,128]

# with open('lapoflap.npy', 'rb') as f:
#     time_lapoflap = np.load(f)
#
# with open('vertical_blur.npy', 'rb') as f:
#     time_blur = np.load(f)
#
# with open('copy_stencil.npy', 'rb') as f:
#     time_copy = np.load(f)
#
# with open('numpy_lapoflap.npy', 'rb') as f:
#     time_lapoflap_np = np.load(f)
#
# with open('numpy_vertical_blur.npy', 'rb') as f:
#     time_blur_np = np.load(f)
#
# with open('numpy_copy_stencil.npy', 'rb') as f:
#     time_copy_np = np.load(f)

with open('novecto_lapoflap.npy', 'rb') as f:
    novect = np.load(f)

with open('noopenmp_lapoflap.npy', 'rb') as f:
    noopenmp = np.load(f)

with open('nounroll_lapoflap.npy', 'rb') as f:
    nounroll = np.load(f)

with open('lapoflap.npy', 'rb') as f:
    lapoflap = np.load(f)

# plt.plot(inpute_sizes,time_lapoflap,marker=symbols[0],linewidth=1,color=colors[0],markersize=3.7,label="lapoflap")
# plt.plot(inpute_sizes,time_copy,marker=symbols[0],linewidth=1,color=colors[1],markersize=3.7,label="copy")
# plt.plot(inpute_sizes,time_blur,marker=symbols[0],linewidth=1,color=colors[2],markersize=3.7,label="vertical blur")
# plt.plot(inpute_sizes,time_lapoflap_np,marker=symbols[2],linewidth=1,color=colors[3],markersize=3.7,label="lapoflap numpy")
# plt.plot(inpute_sizes,time_copy_np,marker=symbols[2],linewidth=1,color=colors[4],markersize=3.7,label="copy numpy")
# plt.plot(inpute_sizes,time_blur_np,marker=symbols[2],linewidth=1,color=colors[5],markersize=3.7,label="vertical blur numpy")

plt.plot(inpute_sizes,lapoflap,marker=symbols[0],linewidth=1,color=colors[0],markersize=3.7,label="openmp")
plt.plot(inpute_sizes,noopenmp,marker=symbols[1],linewidth=1,color=colors[1],markersize=3.7,label="vectorized instructions")
plt.plot(inpute_sizes,novect,marker=symbols[2],linewidth=1,color=colors[2],markersize=3.7,label="unrolling")
plt.plot(inpute_sizes,nounroll,marker=symbols[3],linewidth=1,color=colors[4],markersize=3.7,label="no optimisation")

# plt.legend(ncol=2, fontsize='small')
plt.legend()
plt.subplots_adjust(top=0.75)
plt.suptitle("Time to run 512 iterations of lapoflap with different optimisations\nIntel(R) Xeon(R) CPU E5-2690 v3 2.60GHz\nGCC 9.3.0 -O3",x=0.123,y=0.95,fontname=font,ha='left',fontweight='bold')
plt.title("Time [s]",loc='left',fontname=font)
plt.xlabel("Input size",fontname=font,fontsize='large',fontweight='normal')
# plt.ylim(2**-10,2**10)
plt.tick_params(axis='y',which='both',left=False,right=False)
plt.xscale('log',base=2)
plt.yscale('log',base=2)
#
for pos in ['right', 'top', 'left']:
    plt.gca().spines[pos].set_visible(False)
plt.grid(b=True,which='major',axis='y',c='w')

plt.savefig("timming_opti.pdf")
