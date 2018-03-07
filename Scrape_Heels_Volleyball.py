
# coding: utf-8

# In[144]:


import json
import re

import requests
import scrapy


# In[145]:


headers = {'User-Agent': 'UNC Journo Class'}


# In[146]:


base_url = 'http://goheels.com'
url = base_url + '/roster.aspx?path=wvball'


# In[147]:


resp = requests.get(url, headers=headers)


# In[148]:


body_str = resp.content.decode('utf-8')


# In[149]:


sel = scrapy.Selector(text=body_str)


# In[150]:


table = sel.css('table')[0]


# In[151]:


table


# In[152]:


cols = table.css('th').xpath('string()').extract()


# In[153]:


cols


# In[174]:


rows = table.css('tr')[1:]


# In[175]:


players = []
for r in rows:
    data = {}
    for i, d in enumerate(r.css('td')):
        a = d.css('a')
        if a:
            t = a.xpath('text()').extract_first()
            data['href'] = a.xpath('@href').extract_first()
        else:
            t = d.xpath('text()').extract_first()
        data[cols[i]] = t
    players.append(data)


# In[176]:


players


# In[177]:


def fetch_bio(player):
    player_url = base_url + player['href']
    print('Fetch bio', player_url)
    resp = requests.get(player_url, headers=headers)
    player_txt = resp.content.decode('utf-8')
    sel = scrapy.Selector(text=player_txt)
    player['sel'] = sel
    player['bio'] = sel.css('#sidearm-roster-player-bio').xpath('string()').extract()[0]
    player['img'] = sel.css('.sidearm-roster-player-image img').xpath('@src').extract()[0]


# In[178]:


js_obj_rx = re.compile(r'.*?responsive-roster-bio\.ashx.*?(?P<obj>{.*?})')


# In[179]:


def fetch_stats(player):
    text = player['sel'].xpath('string()').extract()[0]
    parts = text.split('$.getJSON("/services/')[1:]
    captured = js_obj_rx.findall(''.join(parts))
    clean_objs = []
    for obj_str in captured:
        # We only want the stats object...
        if 'stats' not in obj_str:
            continue

        obj_str = obj_str.replace('{', '').replace('}', '')
        obj_str = obj_str.replace("'", '').replace('"', '')
        obj_pairs = obj_str.split(',')
        obj_pairs = [x.split(":") for x in obj_pairs]
        clean_pairs = []
        for pair in obj_pairs:
            clean_pairs.append(['"{}"'.format(p.strip()) for p in pair])
        colonized = [":".join(p) for p in clean_pairs]
        commas = ','.join(colonized)
        json_str = "{" + commas + "}"
        clean_objs.append(json.loads(json_str))
    
    player['stats_url'] = stats_url = (
        "http://goheels.com/services/responsive-roster-bio.ashx?"
        "type={type}&rp_id={rp_id}&path={path}&year={year}"
        "&player_id={player_id}"
    ).format(**clean_objs[0])
    
    print('Fetch stats', stats_url)
    resp = requests.get(stats_url, headers=headers)
    json_stats = json.loads(resp.content.decode("utf-8"))
    player['raw_stats'] = json_stats


# In[180]:


for p in players:
    fetch_bio(p)
    fetch_stats(p)


# In[181]:


players[0]


# In[182]:


txt = p['raw_stats']['career_stats']


# In[183]:


sel = scrapy.Selector(text=txt)
sel


# In[184]:


sel.css('section')


# In[185]:


def parse_stats(player):
    stats = {}
    for raw_key, raw_val in player['raw_stats'].items():
        txt = player['raw_stats'][raw_key]
        if not txt:
            print('Skipping {} for {}'.format(raw_key, player['Full Name']))
            continue
        sel = scrapy.Selector(text=txt)
        # Get all the tables
        for section in sel.css('section'):
            title = section.css('h5').xpath('string()').extract_first()
            cols = section.css('tr')[0].css('th').xpath('string()').extract()
            print('NEW SECTION', title)
            print('COLS', cols)
            these_stats = []
            print('TRS', section.css('tr'))
            for r in section.css('tr')[1:]:
                print('row', r.xpath('string()').extract()[0].replace('\r', '').replace('\n', '').strip())
                s = {}
                for i, d in enumerate(r.css('td'), 0):
                    s[cols[i].lower()] = d.xpath('string()').extract_first()
                yr = r.css('th').xpath('string()')
                if yr:
                    yr = yr.extract()[0]
                    if yr.lower() in ('total', 'season'):
                        print('SKIPPING...')
                        continue
                    print('THE YR IS', yr)
                    s['year'] = yr
                these_stats.append(s)
                print('THE STATS ARE', these_stats)
            existing = stats.get(raw_key, {})
            existing[title] = these_stats
            stats[raw_key] = existing
    player['stats'] = stats


# In[186]:


players[0]


# In[187]:


for p in players:
    parse_stats(p)


# In[188]:


to_dump = [p.copy() for p in players]
for p in to_dump:
    p.pop('sel')
    for k in list(p.keys()):
        if 'raw' in k:
            p.pop(k)
with open('scraped_players.json', 'w') as f:
    json.dump(to_dump, f)


# In[189]:


cat scraped_players.json | cut -c 1-100


# In[190]:


to_dump[0]

