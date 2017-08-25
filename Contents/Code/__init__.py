NAME = 'Sports Are Free'
BASE_URL = 'http://sportsarefree.xyz'
EPG_URL = '%s/listings.json' % (BASE_URL)
HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.12; rv:55.0) Gecko/20100101 Firefox/55.0', 'Referer': BASE_URL}
ICON = 'icon-default.jpg'
ART = 'art-default.jpg'

RE_MAINURL = Regex('var mainurl = "([^"]+)";')
RE_SOURCE = Regex('source: prefix\+"([^"]+)"')

####################################################################################################
def Start():

	ObjectContainer.title1 = NAME

####################################################################################################
@handler('/video/sportsarefree', NAME, art=ART, thumb=ICON)
def MainMenu():

	oc = ObjectContainer()

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
