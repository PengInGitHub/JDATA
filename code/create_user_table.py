#-*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from collections import Counter

root = '/Users/pengchengliu/Documents/GitHub/JDATA2017/'
ACTION_201602_FILE = root+"data/JData_Action_201602.csv"
ACTION_201603_FILE = root+"data/JData_Action_201603.csv"
ACTION_201604_FILE = root+"data/JData_Action_201604.csv"
COMMENT_FILE = root+"data/JData_Comment.csv"
PRODUCT_FILE = root+"/data/JData_Product.csv"
USER_FILE = root+"data/JData_User.csv"
NEW_USER_FILE = root+"data/JData_User_New.csv"
USER_TABLE_FILE = root+"data/user_table.csv"

def get_from_jdata_user():
    # read from NEW_USER_FILE instead of USER_FILE
    # this is b/c NEW_USER_FILE contains processed age col
    # in this sense, run this file after running explore_data.py
    # where NEW_USER_FILE is generated
    # especially the func of tranform_user_age()
    df_usr = pd.read_csv(NEW_USER_FILE, header=0)
    df_usr = df_usr[["user_id", "age", "sex", "user_lv_cd"]]
    return df_usr


# apply type count
def add_type_count(group):
    behavior_type = group.type.astype(int)
    type_cnt = Counter(behavior_type)
    # count type frequency per user
    group['browse_num'] = type_cnt[1]
    group['addcart_num'] = type_cnt[2]
    group['delcart_num'] = type_cnt[3]
    group['buy_num'] = type_cnt[4]
    group['favor_num'] = type_cnt[5]
    group['click_num'] = type_cnt[6]

    return group[['user_id', 'browse_num', 'addcart_num',
                  'delcart_num', 'buy_num', 'favor_num',
                  'click_num']]


def get_from_action_data(fname, chunk_size=100000):
    reader = pd.read_csv(fname, header=0, iterator=True)
    chunks = []
    loop = True
    while loop:
        try:
            chunk = reader.get_chunk(chunk_size)[["user_id", "type"]]
            chunks.append(chunk)
        except StopIteration:
            loop = False
            print("Iteration is stopped")

    df_ac = pd.concat(chunks, ignore_index=True)

    df_ac = df_ac.groupby(['user_id'], as_index=False).apply(add_type_count)
    # Select unique row
    # use pandas df.drop_duplicates()
    df_ac = df_ac.drop_duplicates('user_id')

    return df_ac


def merge_action_data():
    df_ac = []
    # combine behavior data for three months
    df_ac.append(get_from_action_data(fname=ACTION_201602_FILE))
    df_ac.append(get_from_action_data(fname=ACTION_201603_FILE))
    df_ac.append(get_from_action_data(fname=ACTION_201604_FILE))

    # to pandas df
    df_ac = pd.concat(df_ac, ignore_index=True)
    # group by user_id, calculate sum
    df_ac = df_ac.groupby(['user_id'], as_index=False).sum()

    # calculate conversion rates
    # from add cart to purchase
    df_ac['buy_addcart_ratio'] = df_ac['buy_num'] / df_ac['addcart_num']
    # from browse to purchase
    df_ac['buy_browse_ratio'] = df_ac['buy_num'] / df_ac['browse_num']
    # from click to purchase
    df_ac['buy_click_ratio'] = df_ac['buy_num'] / df_ac['click_num']
    # from add favourite to purchase
    df_ac['buy_favor_ratio'] = df_ac['buy_num'] / df_ac['favor_num']

    # strip ratios higher than 1 to 1
    df_ac.ix[df_ac['buy_addcart_ratio'] > 1., 'buy_addcart_ratio'] = 1.
    df_ac.ix[df_ac['buy_browse_ratio'] > 1., 'buy_browse_ratio'] = 1.
    df_ac.ix[df_ac['buy_click_ratio'] > 1., 'buy_click_ratio'] = 1.
    df_ac.ix[df_ac['buy_favor_ratio'] > 1., 'buy_favor_ratio'] = 1.

    return df_ac


if __name__ == "__main__":

    user_base = get_from_jdata_user()
    user_behavior = merge_action_data()

    # SQL: left join
    # user_base: basic user table from User_New table
    # user_behavior, from merge_action_data()
    user_behavior = pd.merge(
        user_base, user_behavior, on=['user_id'], how='left')

    user_behavior.to_csv(USER_TABLE_FILE, index=False)
