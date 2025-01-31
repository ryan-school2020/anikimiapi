from requests_html import HTMLSession
from bs4 import BeautifulSoup
import requests
from anikimiapi.data_classes import *
from anikimiapi.error_handlers import *
import re

class AniKimi:
    """The `AniKimi` class which authorizes the gogoanime client.

    Parameters:
        gogoanime_token (``str``):
            To get this token, please refer to readme.md in the repository.
        auth_token (``str``):
            To get this token, please refer to readme.md in the repository.
        host (``str``):
            Change the base url, If gogoanime changes the domain, replace the url
            with the new domain. Defaults to https://gogoanime.pe/ .
        user_agent (``dict``):
             user_agent header for requests to the host. no need to set/change this.

    Example:
        .. code-block:: python
            :emphasize-lines: 1,4-7

            from anikimiapi import AniKimi

            # Authorize the api to GogoAnime
            anime = AniKimi(
                gogoanime_token="baikdk32hk1nrek3hw9",
                auth_token="NCONW9H48HNFONW9Y94NJT49YTHO45TU4Y8YT93HOGFNRKBI"
            )



    """
    def __init__(
            self,
            gogoanime_token: str,
            auth_token: str, 
            host: str = "https://gogoanime.pe/",
            user_agent:dict = {'User-Agent': 'Mozilla/5.0'},
    ):
        self.gogoanime_token = gogoanime_token
        self.auth_token = auth_token
        self.host = host
        self.user_agent=user_agent

    def __str__(self) -> str:
        return "Anikimi API - Copyrights (c) 2020-2021 BaraniARR."


    def search_anime(self, query: str) -> list:
        """The method used to search anime when a query string is passed

        Parameters:
            query(``str``):
                The query String which was to be searched in the API.

        Returns:
            List of :obj:`-anikimiapi.data_classes.ResultObject`: On Success, the list of search results is returned.

        Example:
        .. code-block:: python
            :emphasize-lines: 1,4-7,10-13

            from anikimiapi import AniKimi

            # Authorize the api to GogoAnime
            anime = AniKimi(
                gogoanime_token="baikdk32hk1nrek3hw9",
                auth_token="NCONW9H48HNFONW9Y94NJT49YTHO45TU4Y8YT93HOGFNRKBI"
            )

            # Get search Results
            search_results = anime.search_anime(query="clannad")
            for results in search_results:
                print(results.title)
                print(results.animeid)

        """
        try:
            url1 = f"{self.host}/search.html?keyword={query}"
            session = HTMLSession()
            response = session.get(url1,headers=self.user_agent)
            response_html = response.text
            soup = BeautifulSoup(response_html, 'html.parser')
            animes = soup.find("ul", {"class": "items"}).find_all("li")
            res_list_search = []
            for anime in animes:  # For every anime found
                tit = anime.a["title"]
                urll = anime.a["href"]
                r = urll.split('/')
                res_list_search.append(ResultObject(title=f"{tit}", animeid=f"{r[2]}"))
            if not res_list_search:
                raise NoSearchResultsError("No Search Results found for the query")
            else:
                return res_list_search
        except requests.exceptions.ConnectionError:
            raise NetworkError("Unable to connect to the Server, Check your connection")

    def get_details(self, animeid: str) -> MediaInfoObject:
        """Get the basic details of anime using an animeid parameter.

        Parameters:
            animeid(``str``):
                The animeid of the anime which you want to get the details.

        Returns:
            :obj:`-anikimiapi.data_classes.MediaInfoObject`: On success, the details of anime is returned as ``MediaInfoObject`` object.

        Example:
        .. code-block:: python
            :emphasize-lines: 1,4-7,10-12

            from anikimiapi import AniKimi

            # Authorize the api to GogoAnime
            anime = AniKimi(
                gogoanime_token="baikdk32hk1nrek3hw9",
                auth_token="NCONW9H48HNFONW9Y94NJT49YTHO45TU4Y8YT93HOGFNRKBI"
            )

            # Get anime Details
            details = anime.get_details(animeid="clannad-dub")
            print(details.image_url) # gives the url of the cover image
            print(details.status) # gives the status whether airing or completed

            # And many more...
        """
        try:
            animelink = f'{self.host}category/{animeid}'
            response = requests.get(animelink,headers=self.user_agent)
            plainText = response.text
            soup = BeautifulSoup(plainText, "lxml")
            source_url = soup.find("div", {"class": "anime_info_body_bg"}).img
            imgg = source_url.get('src')
            tit_url = soup.find("div", {"class": "anime_info_body_bg"}).h1.string
            lis = soup.find_all('p', {"class": "type"})
            plot_sum = lis[1]
            pl = plot_sum.get_text().split(':')
            pl.remove(pl[0])
            sum = ""
            plot_summary = sum.join(pl)
            type_of_show = lis[0].a['title']
            ai = lis[2].find_all('a')  # .find_all('title')
            genres = []
            for link in ai:
                genres.append(link.get('title'))
            year1 = lis[3].get_text()
            year2 = year1.split(" ")
            year = year2[1]
            status = lis[4].a.get_text()
            oth_names = lis[5].get_text()
            lnk = soup.find(id="episode_page")
            ep_str = str(lnk.contents[-2])
            a_tag = ep_str.split("\n")[-2]
            a_tag_sliced = a_tag[:-4].split(">")
            last_ep_range = a_tag_sliced[-1]
            y = last_ep_range.split("-")
            ep_num = y[-1]
            res_detail_search = MediaInfoObject(
                title=f"{tit_url}",
                year=int(year),
                other_names=f"{oth_names}",
                season=f"{type_of_show}",
                status=f"{status}",
                genres=genres,
                episodes=int(ep_num),
                image_url=f"{imgg}",
                summary=f"{plot_summary}"
            )
            return res_detail_search
        except AttributeError:
            raise InvalidAnimeIdError("Invalid animeid given")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Unable to connect to the Server, Check your connection")

    def get_episode_link_advanced(self, animeid: str, episode_num: int) -> MediaLinksObject:
        """Get streamable and downloadable links for a given animeid and episode number.
        If the link is not found, then this method will return ``None`` .

        Parameters:
             animeid(``str``):
                The animeid of the anime you want to download.

             episode_num(``int``):
                The episode number of the anime you want to download.

        Returns:
            :obj:`-anikimiapi.data_classes.MediaLinksObject`: On success, the links of the anime is returned.

        Example:
        .. code-block:: python
            :emphasize-lines: 1,4-7,10-13

            from anikimiapi import AniKimi

            # Authorize the api to GogoAnime
            anime = AniKimi(
                gogoanime_token="baikdk32hk1nrek3hw9",
                auth_token="NCONW9H48HNFONW9Y94NJT49YTHO45TU4Y8YT93HOGFNRKBI"
            )

            # Get anime Link
            link = anime.get_episode_link(animeid="clannad-dub", episode_num=3)
            print(link.link_hdp)
            print(link.link_360p)
            print(link.link_streamtape)

            # and many more...
        """
        try:
            ep_num_link_get = episode_num
            str_qry_final = animeid
            animelink = f'{self.host}category/{str_qry_final}'
            response = requests.get(animelink,headers=self.user_agent)
            plainText = response.text
            soup = BeautifulSoup(plainText, "lxml")
            lnk = soup.find(id="episode_page")
            source_url = lnk.find("li").a
            anime_title = soup.find("div", {"class": "anime_info_body_bg"}).h1.string
            ep_num_tot = source_url.get("ep_end")
            last_ep = int(ep_num_tot)
            episode_url = '{}{}-episode-{}'
            url = episode_url.format(self.host, str_qry_final, ep_num_link_get)
            master_keyboard_list = []
            cookies = {
                'gogoanime': self.gogoanime_token,
                'auth': self.auth_token
            }
            response = requests.get(url=url, cookies=cookies,headers=self.user_agent)
            plaintext = response.text
            soup = BeautifulSoup(plaintext, "lxml")
            download_div = soup.find("div", {'class': 'cf-download'}).findAll('a')
            links_final = MediaLinksObject()
            for links in download_div:
                download_links = links['href']
                q_name_raw = links.text.strip()
                q_name_raw_list = q_name_raw.split('x')
                quality_name = q_name_raw_list[1]  # 360, 720, 1080p links .just append to keyb lists with name and href
                if quality_name == "360":
                    links_final.link_360p = download_links
                elif quality_name == "480":
                    links_final.link_480p = download_links
                elif quality_name == "720":
                    links_final.link_720p = download_links
                elif quality_name == "1080":
                    links_final.link_1080p = download_links
            anime_multi_link_initial = soup.find('div', {'class': 'anime_muti_link'}).findAll('li')
            anime_multi_link_initial.remove(anime_multi_link_initial[0])
            chumma_list = []
            for l in anime_multi_link_initial:
                get_a = l.find('a')
                video_links = get_a['data-video']
                valid = video_links[0:4]
                if valid == "http":
                    pass
                else:
                    video_links = f"https:{video_links}"
                chumma_list.append(video_links)
            anime_multi_link_initial.remove(anime_multi_link_initial[0])
            for other_links in anime_multi_link_initial:
                get_a_other = other_links.find('a')
                downlink = get_a_other['data-video']  # video links other websites
                quality_name = other_links.text.strip().split('C')[0]  # other links name quality
                if quality_name == "Streamsb":
                    links_final.link_streamsb = downlink
                elif quality_name == "Xstreamcdn":
                    links_final.link_xstreamcdn = downlink
                elif quality_name == "Streamtape":
                    links_final.link_streamtape = downlink
                elif quality_name == "Mixdrop":
                    links_final.link_mixdrop = downlink
                elif quality_name == "Mp4Upload":
                    links_final.link_mp4upload = downlink
                elif quality_name == "Doodstream":
                    links_final.link_doodstream = downlink
            res = requests.get(chumma_list[0],headers=self.user_agent)
            plain = res.text
            s = BeautifulSoup(plain, "lxml")
            t = s.findAll('script')
            hdp_js = t[2].string
            hdp_link_initial = re.search("(?P<url>https?://[^\s]+)", hdp_js).group("url")
            hdp_link_initial_list = hdp_link_initial.split("'")
            hdp_link_final = hdp_link_initial_list[0]  # final hdp links
            links_final.link_hdp = hdp_link_final
            return links_final
        except AttributeError:
            raise InvalidAnimeIdError("Invalid animeid or episode_num given")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Unable to connect to the Server, Check your connection")
        except TypeError:
            raise InvalidTokenError("Invalid tokens passed, Check your tokens")

    def get_episode_link_basic(self, animeid: str, episode_num: int) -> MediaLinksObject():
        """Get streamable and downloadable links for a given animeid and episode number.
        If the link is not found, then this method will return ``None`` .

        Parameters:
             animeid(``str``):
                The animeid of the anime you want to download.

             episode_num(``int``):
                The episode number of the anime you want to download.

        Returns:
            :obj:`-anikimiapi.data_classes.MediaLinksObject`: On success, the links of the anime is returned.

        Example:
        .. code-block:: python
            :emphasize-lines: 1,4-7,10-13

            from anikimiapi import AniKimi

            # Authorize the api to GogoAnime
            anime = AniKimi(
                gogoanime_token="baikdk32hk1nrek3hw9",
                auth_token="NCONW9H48HNFONW9Y94NJT49YTHO45TU4Y8YT93HOGFNRKBI"
            )

            # Get anime Link
            link = anime.get_episode_link(animeid="clannad-dub", episode_num=3)
            print(link.link_hdp)
            print(link.link_360p)
            print(link.link_streamtape)

            # and many more...
        """
        try:
            animelink = f'{self.host}category/{animeid}'
            response = requests.get(animelink,headers=self.user_agent)
            plainText = response.text
            soup = BeautifulSoup(plainText, "lxml")
            lnk = soup.find(id="episode_page")
            source_url = lnk.find("li").a
            tit_url = soup.find("div", {"class": "anime_info_body_bg"}).h1.string
            URL_PATTERN = '{}{}-episode-{}'
            url = URL_PATTERN.format(self.host, animeid, episode_num)
            srcCode = requests.get(url,headers=self.user_agent)
            plainText = srcCode.text
            soup = BeautifulSoup(plainText, "lxml")
            source_url = soup.find("li", {"class": "dowloads"}).a
            vidstream_link = source_url.get('href')
            # print(vidstream_link)
            URL = vidstream_link
            dowCode = requests.get(URL,headers=self.user_agent)
            data = dowCode.text
            soup = BeautifulSoup(data, "lxml")
            dow_url= soup.findAll('div',{'class':'dowload'})
            episode_res_link = {'title':f"{tit_url}"}
            links_final = MediaLinksObject()
            for i in range(len(dow_url)):
                Url = dow_url[i].find('a')
                downlink = Url.get('href')
                str_= Url.string
                str_spl = str_.split()
                str_spl.remove(str_spl[0])
                str_original = ""
                quality_name = str_original.join(str_spl)
                episode_res_link.update({f"{quality_name}":f"{downlink}"})
                if "(HDP-mp4)" in quality_name:
                    links_final.link_hdp = downlink
                elif "(SDP-mp4)" in quality_name:
                    links_final.link_sdp = downlink
                elif "(360P-mp4)" in quality_name:
                    links_final.link_360p = downlink
                elif "(720P-mp4)" in quality_name:
                    links_final.link_720p = downlink
                elif "(1080P-mp4)" in quality_name:
                    links_final.link_1080p = downlink
                elif "Streamsb" in quality_name:
                    links_final.link_streamsb = downlink
                elif "Xstreamcdn" in quality_name:
                    links_final.link_xstreamcdn = downlink
                elif "Streamtape" in quality_name:
                    links_final.link_streamtape = downlink
                elif "Mixdrop" in quality_name:
                    links_final.link_mixdrop = downlink
                elif "Mp4Upload" in quality_name:
                    links_final.link_mp4upload = downlink
                elif "Doodstream" in quality_name:
                    links_final.link_doodstream = downlink
            return links_final
        except AttributeError:
            raise InvalidAnimeIdError("Invalid animeid or episode_num given")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Unable to connect to the Server, Check your connection")
        except TypeError:
            raise InvalidTokenError("Invalid tokens passed, Check your tokens")            
        
    def get_by_genres(self,genre_name, limit=60 ) -> list :

        """Get anime by genres, The genre object has the following genres working,

        action, adventure, cars, comedy, dementia, demons, drama, dub, ecchi, fantasy,
        game, harem, hentai - Temporarily Unavailable, historical, horror, josei, kids,
        magic, martial-arts, mecha, military, music, mystery, parody, police, psychological,
        romance, samurai, school, sci-fi, seinen, shoujo, shoujo-ai, shounen-ai, shounen,
        slice-of-life, space, sports, super-power, supernatural, thriller, vampire,
        yaoi, yuri.

        Parameters:
            genre_name(``str``):
                The name of the genre. You should use any from the above mentioned genres.

            limit(``int``):
                The limit for the number of anime you want from the results. defaults to 60 (i.e, 3 pages)

        Returns:
            List of :obj:`-anikimiapi.data_classes.ResultObject`: On Success, the list of genre results is returned.

        Example:
        .. code-block:: python
            :emphasize-lines: 1,4-7,10-13

            from anikimiapi import AniKimi

            # Authorize the api to GogoAnime
            anime = AniKimi(
                gogoanime_token="baikdk32hk1nrek3hw9",
                auth_token="NCONW9H48HNFONW9Y94NJT49YTHO45TU4Y8YT93HOGFNRKBI"
            )

            # Get anime by genre
            get_genre = anime.get_by_genres(genre_name="romance", page=1)
            for result in get_genre:
                print(result.title)
                print(result.animeid)
        """
        gen_ani = []

        def page_anime_scraper(soup_object) -> list:
            """a helper function to scrape anime results from page source"""
            ani_results = []
            animes = soup_object.find("ul", {"class": "items"}).find_all("li")
            for anime in animes:
                tits = anime.a["title"]
                urll = anime.a["href"]
                r = urll.split('/')
                ani_results.append(ResultObject(title=f"{tits}", animeid=f"{r[2]}"))
            return ani_results

        def pagination_helper(current_page_source : str,url,limit:int) -> None:
            """a recursive helper function which helps to successively scrape anime from following pages
                 (if there are any) till limit is reached. """
            soup = BeautifulSoup(current_page_source,"lxml")
            next_page = soup.find("li",{"class": "selected"}).findNext('li')

            
            if (type(next_page) is not None):

                try :

                    [next_page_value] = [i.get('data-page') for i in next_page]
                    next_page_url = f'{url}{next_page_value}'
                    next_page_src = (requests.get(next_page_url,headers=self.user_agent)).text

                    soup = BeautifulSoup(next_page_src,"lxml")

                    #next/subsequent page results
                    next_page_results = page_anime_scraper(soup)
                    for anime in next_page_results:
                        if (len(gen_ani) < limit):
                            gen_ani.append(anime)
                        else:
                            pass
                    if (len(gen_ani) == limit):
                        pass
                    else:
                        pagination_helper(next_page_src,url,limit)

                except AttributeError:
                    pass

            else:
                pass
            
        try:
            url = f"{self.host}genre/{genre_name}?page="
            response =  requests.get(url,headers=self.user_agent)
            plainText = response.text
            soup = BeautifulSoup(plainText,"lxml")
            
            # starting page
            starting_page_results = page_anime_scraper(soup)
            for anime in starting_page_results :
                if (len(gen_ani) < limit):
                    gen_ani.append(anime)
                else:
                    pass

            pagination_helper(current_page_source=plainText,url=url,limit=limit)

            return gen_ani

        except AttributeError or KeyError:
            raise InvalidGenreNameError("Invalid genre_name or page_num")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Unable to connect to server")

    def get_airing_anime(self, count=10) -> list:
        """Get the currently airing anime and their animeid.

        Parameters:
            count(``int`` | ``str``, *optional*):
                The number of search results to be returned, Defaults to 10.

        Returns:
            List of :obj:`-anikimiapi.data_classes.ResultObject`: On Success, the list of currently airing anime results is returned.

        Example:
        .. code-block:: python
            :emphasize-lines: 1,4-7,10-13

            from anikimiapi import AniKimi

            # Authorize the api to GogoAnime
            anime = AniKimi(
                gogoanime_token="baikdk32hk1nrek3hw9",
                auth_token="NCONW9H48HNFONW9Y94NJT49YTHO45TU4Y8YT93HOGFNRKBI"
            )

            airing = anime.get_airing_anime()
            for result in airing:
                print(result.title)
                print(result.animeid)
        """
        try:
            if int(count) >= 20:
                raise CountError("count parameter cannot exceed 20")
            else:
                url = f"{self.host}"
                session = HTMLSession()
                response = session.get(url,headers=self.user_agent)
                response_html = response.text
                soup = BeautifulSoup(response_html, 'html.parser')
                anime = soup.find("nav", {"class": "menu_series cron"}).find("ul")
                air = []
                for link in anime.find_all('a'):
                    airing_link = link.get('href')
                    name = link.get('title')  # name of the anime
                    link = airing_link.split('/')
                    lnk_final = link[2]  # animeid of anime
                    air.append(ResultObject(title=f"{name}", animeid=f"{lnk_final}"))
                return air[0:int(count)]
        except IndexError or AttributeError or TypeError:
            raise AiringIndexError("No content found on the given page number")
        except requests.exceptions.ConnectionError:
            raise NetworkError("Unable to connect to server")
