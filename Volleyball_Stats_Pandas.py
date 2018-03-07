
# coding: utf-8

# In[40]:


import pandas as pd
import numpy as np
import json


# In[41]:


# Pick up from our scraped data
data = json.load(open('scraped_players.json'))


# In[42]:


# Here's an example row. Look at the stats property... it's a nested dictionary
data[0]


# In[43]:


# We need to recreate tables from our data
# We will create dataframes for each permutation of the data
# So we currently have nested data like this:
#
# player (name, position, etc):
#    -> stats
#        -> career_stats
#            -> stats type (hitting / pitching)
#                -> stats for year 1
#                -> stats for year 2
#                -> ...

# We are going to denormalize "grouped" relationship by unrolling them and repeating each level of data
# So our example above becomes
# name, hitting, year 1, stats...
# name, hitting, year 2, stats...
# name, pitching, year 1, stats...
# name, pitching, year 2, stats...
# etc


# In[44]:


# We're going to create a list of stats
data_for_df = []

# We loop over each player in the data we loaded
for player in data:
    # Now we loop over each value in the career_stats items.
    # Not all players have stats so we use `.get` to "defensively" try to get the items
    # So we're saying:
    # give me the stats if it exists, otherwise an empty dictionary
    # Then using that result give me the career_stats key or and empty dictionary
    # and finally the items for the dictionary
    # Note that we can only chain .get and .items because those are attributes on dictionaries
    # and we're defaulting to dictionaries if the item is not found
    for key, val in player.get('stats', {}).get('career_stats', {}).items():
        # Stat type is going from 'Hitting Statistics'
        # to 'hitting statistics'
        # to ['hitting', 'statistics']
        # to 'hitting'
        stat_type = key.lower().split()[0]
        # Players have to have a name and number
        name = player.get('Full Name')
        if not name:
            continue
        num = player.get('#')
        if not num:
            continue
        # Now loop through each value in the career_stats item
        for stat in val:
            # Add the name
            stat['name'] = name
            # Add the player number
            stat['num'] = num
            # Add the stat_type
            stat['stat_type'] = stat_type
            # Append the denormalized row
            # This is now something like
            # {'name': 'John Doe', 'num': '1', 'stat_type': 'hitting', 'year': '2016', ...}
            data_for_df.append(stat)


# In[45]:


# We feed our list of dictionaries into the dataframe class to instantiate a new dataframe
df = pd.DataFrame(data_for_df)
df


# In[48]:


# Attempt to convert everything to a numeric value and by specifying
# errors='ignore' the original value will remain in place if it's not numeric
# Note that this returns a new dataframe so we have to assign it back to our df variable
df = df.apply(pd.to_numeric, errors='ignore')
df


# In[49]:


# Drop the avg stat since it's not always present
# Note this time we can use inplace=True and it does NOT return a new dataframe
# df.drop('avg', axis=1, inplace=True)


# In[50]:


# Generate the batting average and era for all records
# Note again how we have single arithmetic operators
# but our data is a list- this, again, is the power and short cut of pandas / numpy
# df['ba'] = df.h / df.ab
# df['era2'] = df.r / df.ip


# In[62]:


# Now We can generate groups
# We can make a compound group by name and stat type
by_player = df.groupby(('name', 'stat_type'))
# and by year
by_year = df.groupby('year')
# and by type
# by_type = df.groupby('stat_type')
by_player.mean().replace(np.nan, '-', regex=True)


# In[59]:


# We can also group by a property after fetching a group
# Here's the batting average for the whole team by year
by_type.get_group('offensive').groupby('year').mean()


# In[55]:


# Here are all the batting averages across the player / type compound group
# by_player.mean().h / by_player.mean().ab


# In[56]:


# We can mask out the rows where the era2 and ba is null
# and use the .loc method to specify a subset of columns to view
df[df.era2.isnull() & df.ba.isnull()].loc[:, ('name', 'year', 'era', 'ba')]


# In[ ]:


# We can compare that with all the batting averages
df.loc[:, ('name', 'year', 'ba')]


# In[ ]:


# Or all the eras
df.loc[:, ('name', 'year', 'era2')]

