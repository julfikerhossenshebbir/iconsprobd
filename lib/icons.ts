import fs from 'fs';
import path from 'path';

export interface IconDetail {
  body: string;
}

export interface IconsData {
  width: number;
  height: number;
  prefix: string;
  icons: Record<string, IconDetail>;
}

export interface Category {
  label: string;
  keywords: string[];
}

export const CATEGORIES: Record<string, Category> = {
  all:             { label: 'All Icons',       keywords: [] },
  arrows:          { label: 'Arrows',          keywords: ['arrow','chevron','caret','direction','sort','transfer','alt-arrow','double-alt','round-arrow','square-arrow'] },
  'arrows-action': { label: 'Arrows Action',   keywords: ['refresh','restart','reload','rotate','undo','redo','sync','reverse'] },
  messages:        { label: 'Messages',        keywords: ['chat','message','dialog','inbox','letter','mail','plain','paperclip','unread','forward','reply'] },
  map:             { label: 'Map',             keywords: ['map','compass','location','gps','navigation','route','pin','place','people-nearby'] },
  video:           { label: 'Video',           keywords: ['video','camera','film','movie','play','pause','record','stream','reel','clapperboard'] },
  money:           { label: 'Money',           keywords: ['money','wallet','coin','currency','dollar','payment','bank','finance','cash','card','price','pay'] },
  devices:         { label: 'Devices',         keywords: ['phone','mobile','laptop','computer','tablet','device','screen','monitor','keyboard','mouse','printer','server'] },
  weather:         { label: 'Weather',         keywords: ['weather','sun','cloud','rain','snow','wind','storm','fog','temperature','lightning','moon','sky'] },
  files:           { label: 'Files',           keywords: ['file','document','pdf','doc','zip','download','upload','attachment','clip','page'] },
  astronomy:       { label: 'Astronomy',       keywords: ['star','planet','moon','space','galaxy','orbit','telescope','asteroid','comet','solar','universe'] },
  folders:         { label: 'Folders',         keywords: ['folder','directory','archive','library','collection','bookmark'] },
  faces:           { label: 'Faces',           keywords: ['face','emoji','smile','sad','happy','emotion','mood','avatar','head','expression'] },
  search:          { label: 'Search',          keywords: ['search','find','magnify','explore','scan','filter','zoom'] },
  sports:          { label: 'Sports',          keywords: ['sport','ball','football','basketball','tennis','soccer','gym','fitness','run','swim','medal','trophy','game'] },
  time:            { label: 'Time',            keywords: ['time','clock','alarm','timer','calendar','date','schedule','watch','hour','minute'] },
  'list-ui':       { label: 'List UI',         keywords: ['list','grid','menu','table','row','column','layout','sidebar','panel','widget','ui','view','dashboard'] },
  call:            { label: 'Call',            keywords: ['call','phone','dial','contact','voip','receiver','headset','handset'] },
  medicine:        { label: 'Medicine',        keywords: ['medicine','health','hospital','pill','drug','doctor','medical','heart','pulse','ambulance','stethoscope','virus','vaccine'] },
  home:            { label: 'Home & IT',       keywords: ['home','house','door','window','sofa','room','kitchen','wifi','router','cable','signal','network','server','cloud'] },
  settings:        { label: 'Settings',        keywords: ['setting','config','gear','wrench','tool','option','adjust','preference','control','switch','toggle'] },
  'text-formatting':{ label: 'Text Formatting',keywords: ['text','font','bold','italic','underline','align','paragraph','heading','list','quote','link','code','format','type'] },
  business:        { label: 'Business',        keywords: ['business','office','briefcase','work','project','chart','graph','analytics','report','meeting','presentation','target'] },
  shopping:        { label: 'Shopping',        keywords: ['shop','cart','bag','store','buy','product','order','checkout','coupon','gift','sale','discount'] },
  nature:          { label: 'Nature',          keywords: ['nature','tree','leaf','flower','plant','animal','bird','ocean','mountain','river','eco','green'] },
  school:          { label: 'School',          keywords: ['school','book','education','learn','study','pen','pencil','notebook','class','teacher','student','graduation','library'] },
  tools:           { label: 'Tools',           keywords: ['tool','hammer','screwdriver','drill','saw','wrench','fix','repair','build','construct'] },
  food:            { label: 'Food',            keywords: ['food','drink','eat','restaurant','coffee','tea','cake','fruit','vegetable','cook','kitchen','recipe','meal'] },
  like:            { label: 'Like',            keywords: ['like','love','heart','favorite','star','rating','thumbs','reaction','vote','bookmark','save'] },
  notes:           { label: 'Notes',           keywords: ['note','memo','sticky','pad','write','edit','annotation','comment','label','tag'] },
  notifications:   { label: 'Notifications',  keywords: ['notification','bell','alert','badge','reminder','announce','warning','info'] },
  security:        { label: 'Security',        keywords: ['security','lock','shield','key','password','private','protect','safe','virus','firewall','encrypt','auth'] },
  users:           { label: 'Users',           keywords: ['user','people','person','profile','account','team','group','member','contact','friend'] },
  building:        { label: 'Building',        keywords: ['building','office','bank','hotel','hospital','school','city','house','store','factory','skyscraper'] },
  'hands-parts':   { label: 'Hands & Parts',  keywords: ['hand','finger','thumb','gesture','body','arm','eye','ear','mouth','touch','point','wave'] },
};

let _cache: IconsData | null = null;

export function loadIcons(): IconsData {
  if (_cache) return _cache;
  const filePath = path.join(process.cwd(), 'public', 'icons.json');
  if (!fs.existsSync(filePath)) {
    return { width: 24, height: 24, prefix: 'icons', icons: {} };
  }
  const raw = fs.readFileSync(filePath, 'utf-8');
  _cache = JSON.parse(raw) as IconsData;
  return _cache;
}
