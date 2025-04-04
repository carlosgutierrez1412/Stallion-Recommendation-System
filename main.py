import pandas as pd
from stallion_recomender import recommend_stallions

df = pd.read_csv("Data\cleaned\Horse_Data_Cleaned.csv")

if __name__ == "__main__":
    mare_name = input("Enter the name of the mare: ")
    recommend_stallions(df, mare_name)
    print("\n\n")
