import pandas as pd
import glob

# Specify the path to your CSV files
path = "data/"  # Adjust this path
all_files = glob.glob(path + "*.csv")

# Load all CSV files into a list of DataFrames
dfs = []
for filename in all_files:
    df = pd.read_csv(filename)
    dfs.append(df)

# Concatenate all DataFrames into a single DataFrame
merged_df = pd.concat(dfs, ignore_index=True)

# Display the shape of the merged DataFrame
print("Shape of merged DataFrame:", merged_df.shape)

# Display the first few rows of the DataFrame
print(merged_df.head())

# EDA: Display information about the DataFrame
print(merged_df.info())

# Check for missing values
print("Missing values in each column:")
print(merged_df.isnull().sum())

# EDA: Descriptive statistics for numerical columns
print("Descriptive statistics:")
print(merged_df.describe())

# Preprocessing: Convert 'created_at' to datetime
merged_df['created_at'] = pd.to_datetime(merged_df['created_at'])

# Drop duplicates
merged_df.drop_duplicates(inplace=True)

# Reset index after dropping duplicates
merged_df.reset_index(drop=True, inplace=True)

# Example: Filter tweets with more than a certain number of likes
popular_tweets = merged_df[merged_df['like_count'] > 10]
print("Popular tweets:")
print(popular_tweets)

# Save the cleaned and merged DataFrame to a new CSV
merged_df.to_csv("merged_twitter_data.csv", index=False)
