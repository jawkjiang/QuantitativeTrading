import pandas as pd
import os

dataframe = pd.DataFrame()
for directories in os.listdir('data'):
    if os.path.isdir(f'data/{directories}'):
        datalist = []
        for i in range(100):
            df = pd.read_csv(f'data/{directories}/{directories}-{1680259200000+300000*1000*i}.csv')
            for j in range(1000):
                if 1680259200000+300000*1000*i+j*300000 in df['timestamp'].values:
                    datalist.append(df[df['timestamp'] == 1680259200000+300000*1000*i+j*300000]['open'].values[0])
                else:
                    datalist.append(0)
            print(len(datalist))
        dataframe[directories] = datalist
    print(dataframe)

dataframe.to_csv('data/combined.csv', index=False)
