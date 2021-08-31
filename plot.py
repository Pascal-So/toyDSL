import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def append_df(dataframe, unroll,vectorize, openmp, copy_stencil, vetical_blur,lapoflap):
    dataframe = dataframe.append({'unroll': unroll,
                'vectorize': vectorize,
                'openmp': openmp,
                'copy_stencil': copy_stencil,
                'vertical_blur': vetical_blur,
                'lapoflap': lapoflap}, 
                ignore_index=True)
    return dataframe

if __name__ == "__main__":
    df_sec = pd.DataFrame(columns =('unroll','vectorize','openmp','copy_stencil', 'vertical_blur', 'lapoflap'))
    df_sec = append_df(df_sec,1,False,False, 138.156145648, 604.525416697, 660.082927219)
    df_sec = append_df(df_sec,4,False,False,93.684044494, 200.836122129, 344.995356794)
    df_sec = append_df(df_sec,4,True,False,94.773355536,331.794852993,375.869755695)
    df_sec = append_df(df_sec,4,True,True,11.872591862,36.573046971,52.158416602)
    df_sec = append_df(df_sec,4,False,True,11.361567298,32.427799394,39.9568979)
    df_sec = append_df(df_sec,8,False,True,11.762738518,31.587117513,34.756710882)
    df_sec = append_df(df_sec,8,False,False,90.599052203,183.833517631,300.799992193)

    #print(df_sec)
    plt.figure()
    df_sec.iloc[:,3:6].plot()
    #df_sec.plot(x='vectorize', y='copy_stencil')
    #df_sec.plot(x='arguments', y='vertical_blur')
    #df_sec.plot(ylabel='time in sec', xlabel='parameters')
    #plt.tick_params(axis='x', which='major', labelsize=3)
    #plt.show()
    plt.savefig("plot.png")
    
    ##For latex report
    #print(df_sec.to_latex(index=False))


    # plt.ioff()
    # plt.imshow(input[input.shape[0] // 2, :, :], origin="lower")
    # plt.colorbar()
    # plt.savefig("in_field.png")
    # plt.close()
