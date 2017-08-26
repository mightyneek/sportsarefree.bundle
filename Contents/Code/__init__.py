NAME = 'Sports Are Free'
BASE_URL = 'http://sportsarefree.xyz'
EPG_URL = '%s/listings.json' % (BASE_URL)
HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0', 'Referer': BASE_URL}
ICON = 'icon-default.png'
ART = 'art-default.jpg'

RE_MAINURL = Regex('var mainurl = "([^"]+)";')
RE_SOURCE = Regex('source: prefix\+"([^"]+)"')

####################################################################################################
def Start():

	ObjectContainer.title1 = NAME

	try:
		json_obj = JSON.ObjectFromURL('http://ip-api.com/json', cacheTime=10)
	except:
		Log("ip check failed")
		json_obj = None

	if json_obj and 'countryCode' in json_obj and json_obj['countryCode'] != 'US':
		Log("============================== WARNING ==============================")
		Log("According to your ip address you are not in the United States!")
		Log("This channel does not work outside the United States as stated in the README:")
		Log("https://github.com/piplongrun/sportsarefree.bundle/blob/master/README.md")
		Log("=====================================================================")

####################################################################################################
@handler('/video/sportsarefree', NAME, art=ART, thumb=ICON)
def MainMenu():

	oc = ObjectContainer()
	oc.add(DirectoryObject(key=Callback(NFL), title='NFL', thumb=R(ICON)))

	html = HTML.ElementFromURL(BASE_URL, headers=HTTP_HEADERS, cacheTime=CACHE_1HOUR)
	channel_list = html.xpath('//div[@class="grid-item"]')

	for channel in channel_list:

		title = channel.get('data')
		thumb = channel.xpath('./img/@src')[0]

		id = channel.xpath('./p/@id')[0].split('channel')[-1]
		epg_info = GetEPG(id)

		if epg_info:
			title = '%s: %s' % (title, epg_info)

		oc.add(CreateVideoClipObject(
			title = title,
			thumb = thumb
		))

	return oc

####################################################################################################
@route('/video/sportsarefree/nfl')
def NFL():

	oc = ObjectContainer(title2='NFL')
	oc.add(CreateVideoClipObject(title='nfltv', thumb=R(ICON)))

	html = HTML.ElementFromURL('%s/%s' % (BASE_URL, 'nfl'), headers=HTTP_HEADERS, cacheTime=60)
	channel_list = html.xpath('//span[@data and @class!="date"]')

	for channel in channel_list:

		title = channel.get('data')
		thumb = R(ICON)

		oc.add(CreateVideoClipObject(
			title = title,
			thumb = thumb
		))

	return oc

####################################################################################################
@route('/video/sportsarefree/epg')
def GetEPG(id):

	try:
		json_obj = JSON.ObjectFromURL(EPG_URL, cacheTime=60)['media']
	except:
		# Don't break channel listing if epg call fails
		return None

	for media in json_obj:

		if media['i'] == int(id):
			return media['p'] if media['p'] else None

	return None

####################################################################################################
@route('/video/sportsarefree/createvideoclipobject', include_container=bool)
def CreateVideoClipObject(title, thumb, include_container=False, **kwargs):

	videoclip_obj = VideoClipObject(
		key = Callback(CreateVideoClipObject, title=title, thumb=thumb, include_container=True),
		rating_key = title.split(':')[0],
		title = title,
		thumb = thumb,
		items = [
			MediaObject(
				parts = [
					PartObject(key=HTTPLiveStreamURL(Callback(PlayVideo, id=title.split(':')[0])))
				],
				video_resolution = '720',
				audio_channels = 2,
				optimized_for_streaming = True
			)
		]
	)

	if include_container:
		return ObjectContainer(objects=[videoclip_obj])
	else:
		return videoclip_obj

####################################################################################################
@route('/video/sportsarefree/playvideo.m3u8')
@indirect
def PlayVideo(id, **kwargs):

	url = '%s/%s' % (BASE_URL, id)

	page = HTTP.Request(url, headers=HTTP_HEADERS, cacheTime=CACHE_1HOUR).content

	mainurl = RE_MAINURL.search(page).group(1)
	source = RE_SOURCE.search(page).group(1)

	video_url = '%s%s' % (mainurl, source)

	return IndirectResponse(VideoClipObject, key=video_url)
