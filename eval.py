import requests
from bs4 import BeautifulSoup
import csv
import sqlite3
import pandas as pd
import re
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

def extract_data_to_database(filename, searchnames=None):
    """Extracts all the chat for both person in the chat
    
    Args:
        filename (string): filename
        searchnames (tuple, optional): Two names (Tuple of two strings) to search for. Only for group conversations. Defaults to None.
    """
    # gets the connection to the db
    DB = sqlite3.connect("textdata.db")
    c = DB.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS data(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, name_id INTEGER NOT NULL, message TEXT NOT NULL, date_w DATETIME NOT NULL, relation_id INTEGER);")
    c.execute("CREATE TABLE IF NOT EXISTS names(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL);")
    c.execute("CREATE TABLE IF NOT EXISTS relations(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, relation TEXT NOT NULL);")

    # opens up the file and get all name tags and the text tag for it as well as the dates
    with open(filename, encoding="utf8") as fp:
        soup = BeautifulSoup(fp, "html5lib")
    infotext("Extracting all the HTML Data")
    names = soup.findAll('div', {'class' : '_3-96 _2pio _2lek _2lel'})
    infotext("Namegetting done")
    texts = soup.findAll('div', {'class' : '_3-96 _2let'})
    infotext("Textgetting done")
    dates = soup.findAll('div', {'class' : "_3-94 _2lem"})
    infotext("Dategetting done")

    # depending on the input, gets the both names (if not provided)
    if searchnames is None:
        name1 = names[0].get_text()
        name2 = names[0].get_text()
        for name in names:
            if name.get_text() != name2:
                name2 = name.get_text()
                break
    else:
        name1, name2 = searchnames

    # creates new names and relation in the DB if not exist
    relation1 = f"{name1}-{name2}"
    relation2 = f"{name2}-{name1}"
    rel_exists = c.execute("SELECT id FROM relations WHERE relation = ? OR relation = ?", (relation1,relation2,)).fetchone()
    if rel_exists is None:
        c.execute("INSERT OR IGNORE INTO relations(relation) VALUES(?)",(relation1,))
        DB.commit()
        rel_id = c.execute("SELECT id FROM relations WHERE relation=?", (relation1,)).fetchone()[0]
    else:
        rel_id = rel_exists[0]
    ids = []
    for name in (name1, name2):
        name_exists = c.execute("SELECT id FROM names WHERE name = ?", (name,)).fetchone()
        if name_exists is None:
            c.execute("INSERT OR IGNORE INTO names(name) VALUES(?)",(name,))
            DB.commit()
            ids.append(c.execute("SELECT id FROM names WHERE name=?", (name,)).fetchone()[0])
        else:
            ids.append(name_exists[0])
    id1, id2 = ids

    # assigns the text and the dates to the names, enter it into a db
    name1_text = []
    name2_text = []
    total_textlen = len(names)
    print(f"The total length of the text is: {total_textlen}")
    for name, text, date in zip(names, texts, dates):
        current_name = name.get_text()
        current_text = text.get_text()
        current_date = date.get_text()
        if current_name == name1:
            name1_text.append(current_text)
            enter_id = id1
        elif current_name == name2:
            name2_text.append(current_text)
            enter_id = id2
        # if there are more than two people in the conversation ignore them
        else:
            continue
        c.execute("INSERT INTO data(name_id, message, date_w, relation_id) VALUES(?,?,?,?)",(enter_id, current_text, current_date, rel_id,))

    # commit DB entries and close __init__(self, *args, **kwargs):
    DB.commit()
    DB.close()
    # visualize part of the extracted data
    print_attributes(name1, name2, name1_text, name2_text)

def read_in_data(name1, name2):
    """Get all the needed data from the DB and reads it into a Datastructur
    
    Args:
        name1 (string): Full name of the first person.
        name2 (string): Full name of the second person.

    Returns:
        tuple: Tuple of both dataframes with data of date and text accordingly
    """
    # gets a connection to the DB and gets all the needed ids
    DB = sqlite3.connect("textdata.db")
    c = DB.cursor()
    name1_id = c.execute("SELECT id FROM names WHERE name=?", (name1,)).fetchone()[0]
    name2_id = c.execute("SELECT id FROM names WHERE name=?", (name2,)).fetchone()[0]
    relation1 = f"{name1}-{name2}"
    relation2 = f"{name2}-{name1}"
    relation_id = c.execute("SELECT id FROM relations WHERE relation=? OR relation=?", (relation1,relation2,)).fetchone()[0]

    # informs about the data and the next steps
    infotext("Got all needed ids of the names")
    print(f"Id of {name1}: {name1_id}")
    print(f"Id of {name2}: {name2_id}")
    print(f"Id of {relation1}: {relation_id}")

    # start to get all the data into a fitting structure
    infotext("Reading in all needed Data from DB and generate DF")
    df1 = generate_df_data(name1_id, relation_id, c)
    df2 = generate_df_data(name2_id, relation_id, c)
    infotext("Done with the df")
    return (df1, df2)

def generate_df_data(name, relation, cur):
    """Gets the data out of the DB and returns a DF of the needed values
    
    Args:
        name (int): id of the name to get data.
        relation (id): id the the relation between both names.
        cur (DB.cursor): cursor of the Database.
    
    Returns:
        dataframe: Dataframe with data of date and text accordingly
    """
    text = []
    date = []
    # gets all the data for one name and the corresponding relation
    data = cur.execute("SELECT message, date_w FROM data WHERE name_id=? AND relation_id=?",(name, relation))
    for row in data:
        text.append(row[0])
        date.append(row[1])

    # generates a dict out of the lists and then a DF
    d = {'date': date, 'text': text}
    df = pd.DataFrame(data=d)
    df.date = pd.to_datetime(df.date, format='%d.%m.%Y, %H:%M')
    df["length"] = np.vectorize(length)(df['text'])
    df.set_index("date", inplace=True)
    return df

def plot_most_used_emojis(df1, df2, name1, name2, col1='blue', col2='pink', n=7):
    """Plots a bar plot of the top used emojis
    
    Args:
        name1 (string): Name of the first person.
        name2 (string): Name of the second person.
        col1 (str, optional): Color of the first bar. Defaults to 'blue'.
        col2 (str, optional): Color of the second bar. Defaults to 'pink'.
        n (int, optional): Number of top used emojis. Defaults to 7.
    """
    # generates two dicts for the most used n emojis
    dict1, dict2 = get_most_used_emojis(df1, df2, name1, name2, n)
    # plot two separate bar plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
    ax1.set_xticklabels(dict1.keys(),size=15)
    ax2.set_xticklabels(dict2.keys(),size=15)
    ax1.set_ylabel("Relative number of occurences (%)")
    ax2.set_ylabel("Relative number of occurences (%)")
    ax1.set_title(name1)
    ax2.set_title(name2)
    ax1.bar(dict1.keys(), dict1.values(), color=col1)
    ax2.bar(dict2.keys(), dict2.values(), color=col2)
    plt.get_current_fig_manager().window.state('zoomed')

def get_most_used_emojis(df1, df2, name1, name2, n=7):
    """Summarize the top n most used emojis
    
    Args:
        name1 (string): Name of first person.
        name2 (string): name of second person.
        n (int, optional): Number of top used emojis. Defaults to 7.
    
    Returns:
        tuple: tuple of dicts
    """
    infotext("Calculating proportions")
    top1 = generate_top_n(df1, n)
    top2 = generate_top_n(df2, n)
    print(top1)
    print(top2)
    return (top1, top2)

def generate_top_n(df, n=7):
    """Generates the top n used emojis
    
    Args:
        df (dataframe): Dataframe with the date/text data.
        n (int, optional): Number of top used emojis. Defaults to 7.
    
    Returns:
        dict: Dict with the top n emojis in percantage usage to all existing one.
    """
    # code for the emojis
    exp = re.compile(u'([\U00002600-\U000027BF])|([\U0001f300-\U0001f64F])|([\U0001f680-\U0001f6FF])')
    emojis = exp.findall(''.join(df.text.values))

    # generates a list of all the emojis
    e_list = []
    for l in emojis:
        e_list.append(''.join(l))
    # generates a dict with the counts of each emoji
    e_dict = {}
    for e in e_list:
        if e in e_dict:
            e_dict[e] += 1
        else:
            e_dict[e] = 1

    # normalize them to the total amount
    for key in e_dict.keys():
        e_dict[key] = round((e_dict[key]/len(e_list))*100,4)
    # ranks them by top usage, cut to top n
    top_emoji_dict = dict(sorted([(k,v) for k, v in e_dict.items()], key = lambda x: x[1], reverse=True)[0:n])
    return top_emoji_dict

def plot_day(df1, df2, name1, name2, col1='blue', col2='pink', use_len=False):
    """Plots the different weekdays and their average.
    
    Args:
        df1 (dataframe): Dataframe with the first person data.
        df2 (dataframe): Dataframe with the seconf person data.
        name1 (string): Name of the first person.
        name2 (string): Name of the second person.
        col1 (str, optional): Color for the first person. Defaults to 'blue'.
        col2 (str, optional): Color for the second person. Defaults to 'pink'.
        use_len (bool, optional): Condition for unsing then len or the count. Defaults to False.
    """
    # decides on how to group/sum the values and the title name
    if use_len:
        s1 = df1.groupby(df1.index.weekday).sum().values
        s2 = df2.groupby(df2.index.weekday).sum().values
        title = "Message length by day"
    else:
        s1 = df1.groupby(df1.index.weekday).count().values
        s2 = df2.groupby(df2.index.weekday).count().values
        title = "Message count by day"
    
    # generates a list out of the list in list data
    s1 = [s[0] for s in s1]
    s2 = [s[0] for s in s2]

    # plots the weekdays for both Person. Therefore creates a DF first.
    plotdf = pd.DataFrame({name1: s1, name2: s2})
    fig, ax = plt.subplots()
    plotdf.plot(kind="bar", color=(col1,col2), ax=ax)
    ax.set_xlabel("Weekday")
    ax.set_xticklabels(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Son"], rotation=0)
    ax.axes.get_yaxis().set_visible(False)
    ax.set_title(title)
    ax.set_ylim(0)
    plt.get_current_fig_manager().window.state('zoomed')

def plot_total(df1, df2, name1, name2, col1='blue', col2='pink', use_len=False, area=False):
    """[summary]
    
    Args:
        df1 (dataframe): Dataframe with the first person data.
        df2 (dataframe): Dataframe with the seconf person data.
        name1 (string): Name of the first person.
        name2 (string): Name of the second person.
        col1 (str, optional): Color for the first person. Defaults to 'blue'.
        col2 (str, optional): Color for the second person. Defaults to 'pink'.
        use_len (bool, optional): Condition for unsing then len or the count. Defaults to False.
        area (bool, optional): Condition if the area below the plot should be filled. Defaults to False.
    """
    fig, ax = plt.subplots()
    # decides on grouping and name giving for title
    if use_len:
        df1_val = df1.groupby(df1.index.date).sum()
        df2_val = df2.groupby(df2.index.date).sum()
        title = "Daily message length"
    else:
        df1_val = df1.groupby(df1.index.date).count()
        df2_val = df2.groupby(df2.index.date).count()
        title = "Daily message count"
    
    # plots both series
    df1_val.plot(ax=ax, color=col1, label=name1, alpha=0.5)
    df2_val.plot(ax=ax, color=col2, label=name2, alpha=0.5)
    if area:
        ax.fill_between(df1_val.index, df1_val.length, alpha=0.2, color=col1)
        ax.fill_between(df2_val.index, df2_val.length, alpha=0.2, color=col2)

    # generates a own (better) legend for the plot
    legend_elements = [Patch(facecolor=col1, edgecolor=col1),
                       Patch(facecolor=col2, edgecolor=col2)]
    ax.legend(legend_elements, [name1, name2])
    ax.set_title(title)
    ax.set_ylim(0)
    plt.get_current_fig_manager().window.state('zoomed')

def get_len_prop(df):
    """Gets the avg len, total len and total messages send by the df.
    
    Args:
        df (dataframe): Dataframe with the needed values.
    
    Returns:
        tuple: Tuple with avg text len, total messages and total text len.
    """
    total_len = len(''.join(df.text.values))
    total_text = len(df.text.values)
    average_len = round(total_len/total_text, 1)
    return (average_len, total_text, total_len)

def infotext(text):
    """Nicely formats the text for the output
    
    Args:
        text (string): Output text.
    """
    str_fill = "-"
    print(f"{str_fill} {text} .... {str_fill}")

def print_attributes(name1, name2, name1_text, name2_text):
    """Print out the attributes after the parsing of the html data.
    
    Args:
        name1 (string): First persons name
        name2 (string): Second persons name
        name1_text (list): List of all the messages of first person
        name2_text (list): List of all the messages of the second person
    """
    print(f"{30*'-'} Textdata {30*'-'}")
    print(f"{10*'-'} Content of: {name1} {10*'-'}")
    print(f"Length is: {len(name1_text)}, up to 10 messages:")
    if len(name1_text) > 10:
        print(name1_text[0:9])
    else:
        print(name1_text)
    print(f"{10*'-'} Content of: {name2} {10*'-'}")
    print(f"Length is: {len(name2_text)}, up to 10 messages:")
    if len(name1_text) > 10:
        print(name2_text[0:9])
    else:
        print(name2_text)

def length(x):
    return len(x)

def start_visualisation(name1, name2, col1='blue', col2='pink', n=7):
    """[summary]
    
    Args:
        name1 (string): Name of the first person.
        name2 (string): Name of the second person.
        col1 (str, optional): Color for the first person. Defaults to 'blue'.
        col2 (str, optional): Color for the second person. Defaults to 'pink'.
        n (int, optional): Number of top n Emojis to plot. Defaults to 7.
    """
    df1, df2 = read_in_data(name1, name2)
    plot_most_used_emojis(df1, df2, name1, name2, col1=col1, col2=col2, n=n)
    plot_day(df1, df2, name1, name2, col1=col1, col2=col2)
    plot_day(df1, df2, name1, name2, col1=col1, col2=col2, use_len=True)
    plot_total(df1, df2, name1, name2, col1=col1, col2=col2, area=True)
    plot_total(df1, df2, name1, name2, col1=col1, col2=col2, use_len=True, area=True)
    plt.show()

if __name__ == "__main__":
    # extract_data_to_database("yourname.html")
    # start_visualisation("Name1", "Name2", col1="blue", col2="red")
    pass