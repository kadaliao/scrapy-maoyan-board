# -*- coding: utf-8 -*-
import scrapy
from crawler.items import MovieItem
import os
from fontTools.ttLib import TTFont
from io import BytesIO
import re


class MaoyanSpider(scrapy.Spider):
    name = 'maoyan'
    allowed_domains = ['maoyan.com']
    start_urls = ['http://maoyan.com/board/1']

    basefont_filepath = os.path.abspath(os.path.dirname(__file__)) + '/fonts/base.woff'
    basefont = TTFont(basefont_filepath)
    basefont_codes = basefont.getGlyphOrder()[2:]
    basefont_nums = map(str, [0, 7, 6, 8, 4, 5, 2, 3, 1, 9])
    basefont_code2num = dict(zip(basefont_codes, basefont_nums))

    font_dict = {}

    def extract_font_link(self, html):
        reobj = re.compile("url\('(//*.*.woff)'\) format\(\'woff\'\);")
        results = reobj.findall(html)
        return 'http:' + results[0]

    def parse_font(self, response):
        font = TTFont(BytesIO(response.body))
        font_codes = font.getGlyphOrder()[2:]
        font_code2num = {'.': '.'}

        for font_code in font_codes:
            font_glyf = font['glyf'][font_code]

            for basefont_code in self.basefont_codes:
                basefont_glyf = self.basefont['glyf'][basefont_code]

                if basefont_glyf == font_glyf:
                    # uniF478
                    # \ue6c6
                    key = chr(int(font_code[3:], 16))
                    font_code2num[key] = self.basefont_code2num[basefont_code]

        self.font_dict[response.url] = font_code2num

        print(font_code2num)

        if response.meta['task_name'] == 'board':
            movies = response.meta['movies']
            for movie in movies:
                movie['boxoffice_realtime'] = ''.join([font_code2num[i] for i in movie['boxoffice_realtime']])
                movie['boxoffice_total'] = ''.join([font_code2num[i] for i in movie['boxoffice_total']])
                yield scrapy.Request(movie['link'], callback=self.parse_movie, meta={'movie': movie})

        if response.meta['task_name'] == 'movie':
            movie = response.meta['movie']
            # '\uee6d\uee6d.\ue59b'

            print(movie)

            # movie['score'] = ''.join([font_code2num[i] for i in movie['score']])

            if movie['score']:
                movie['score'] = ''.join([font_code2num[i] for i in movie['score']])

            movie_item = MovieItem(**movie)
            yield movie_item

    def parse(self, response):
        dl = response.css('dd')
        font_link = self.extract_font_link(response.text)
        # print(font_link)

        movies = []
        for dd in dl:
            movie = {}
            movie['name'] = dd.css('.name a::text').extract_first()
            movie['link'] = response.urljoin(dd.css('.name a::attr(href)').extract_first())
            movie['star'] = dd.css('.star::text').extract_first()
            movie['releasetime'] = dd.css('.releasetime::text').extract_first()
            movie['boxoffice_realtime'] = dd.css('.realtime span::text').extract_first()
            movie['boxoffice_total'] = dd.css('.total-boxoffice span::text').extract_first()

            movies.append(movie)

        if font_link in self.font_dict:
            self.process_board(meta={'movies': movies, 'font_code2num': self.font_dict[font_link]})
        else:
            yield scrapy.Request(font_link, callback=self.parse_font, meta={'movies': movies, 'task_name': 'board'},
                                 dont_filter=True)

    def parse_movie(self, response):
        movie = response.meta['movie']
        # movie['score'] = response.css('.score .stonefont::text').extract_first()
        movie['score'] = response.css('.movie-index .score .stonefont::text').extract_first()

        font_link = self.extract_font_link(response.text)
        # print(font_link)

        if font_link in self.font_dict:
            return self.process_movie(meta={'movie': movie, 'font_code2num': self.font_dict[font_link]})

        yield scrapy.Request(font_link, callback=self.parse_font, meta={'task_name': 'movie', 'movie': movie},
                             dont_filter=True)

    def process_movie(self, meta):
        movie = meta['movie']
        font_code2num = meta['font_code2num']
        # '\uee6d\uee6d.\ue59b'
        if movie['score']:
            movie['score'] = ''.join([font_code2num[i] for i in movie['score']])

        movie_item = MovieItem(**movie)
        yield movie_item

    def process_board(self, meta):
        movies = meta['movies']
        font_code2num = meta['font_code2num']
        for movie in movies:
            movie['boxoffice_realtime'] = ''.join([font_code2num[i] for i in movie['boxoffice_realtime']])
            movie['boxoffice_total'] = ''.join([font_code2num[i] for i in movie['boxoffice_total']])
            yield scrapy.Request(movie['link'], callback=self.parse_movie, meta={'movie': movie})
