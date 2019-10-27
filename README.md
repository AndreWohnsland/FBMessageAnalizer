# Facebook text analysis

This script can help you extract and visulize your facebook chat data from any of your contacts. You can display emoji fraction usage, texting behaviour on weekdays or visualize the amount/length of text over the time.

First thing you have to do is to request your chat data from FB in the HTML fromat. IN Facebook go to options > Your Facebook Information > Download Your Information and then select the time period as well as only the messages option. After that you will need to wait up to one day unitl you can download all data. After you unzip the data, the messages are regularly found in the `inbox` folder. There you will see the names of all your contacts. Choose one. Inside this folder there may or may not be various other folder and a `message_1.html`file, the one we are gonna use for the analysis. Put it into the folder with this script. You may rename it to a better fitting name (in case you will use multiple chats). 

First extract the data into the database with `extract_data_to_database("yourname.html")` - this command needs only to be run once, otherwise there will be multiple entries into the DB. This process may take some time depending on the length of your file. In my case the classes of the three needed divs are `_3-96 _2pio _2lek _2lel`, `_3-96 _2let` and `_3-94 _2lem` you can change them in the `extract_data_to_database` if they are different in your HTML file.

Once the data is extracted into the database you run `start_visualisation("Name1", "Name2", col1="blue", col2="red")` with `Name1` and `Name2` as the exact names of both participants. The `generate_df_data` method got a `pd.to_datetime(df.date, format='%d.%m.%Y, %H:%M')` function inside it. The format from your data may differ and i would recommend checkig your format before.

## Minimal Requirements

```
- Python 3.6
- requests
- bs4
- html5lib
- matplotlib 3.1
- pandas
- numpy (included with matplotlib)
```
The packages can usually be installed from PyPi with the `pip install 'packagename'` or your system according command.

## Some impressions

![Countdays]( "Countdays")

![Lendays]( "Lendays")

![Counttotal]( "Counttotal")

![Lentotal]( "Lentotal")
