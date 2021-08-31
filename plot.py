import matplotlib.pyplot as plt
import argparse
import numpy as np

font = "Ubuntu"
symbols = ["D","o","s"]
colors = ["#618DF5","#F56161","#F5A161"]
background = "#e7e4e4"

ax2 = plt.axes()
ax2.set_facecolor(background)

inpute_sizes=[16,32,64,128,256]

with open('lapoflap.npy', 'rb') as f:
    time_lapoflap = np.load(f)

with open('vertical_blur.npy', 'rb') as f:
    time_blur = np.load(f)

# with open('copy_stencil.npy', 'rb') as f:
#     time_copy = np.load(f)

plt.plot(inpute_sizes,time_lapoflap,marker=symbols[0],linewidth=1,color=colors[0],markersize=3.7,label="lapoflap")
# plt.plot(inpute_sizes,time_copy,marker=symbols[1],linewidth=1,color=colors[1],markersize=3.7,label="copy")
plt.plot(inpute_sizes,time_blur,marker=symbols[2],linewidth=1,color=colors[2],markersize=3.7,label="vertical blur")

plt.legend()
plt.subplots_adjust(top=0.80)
plt.suptitle("Time to run 512 iterations of each thing",x=0.123,y=0.95,fontname=font,ha='left',fontweight='bold')
plt.title("Time [s]",loc='left',fontname=font)
plt.xlabel("Input size",fontname=font,fontsize='large',fontweight='normal')
# # plt.ylim(-0.2,3)
plt.tick_params(axis='y',which='both',left=False,right=False)
plt.xscale('log',base=2)
plt.yscale('log',base=2)
#
for pos in ['right', 'top', 'left']:
    plt.gca().spines[pos].set_visible(False)
plt.grid(b=True,which='major',axis='y',c='w')

plt.savefig("timming.png")
