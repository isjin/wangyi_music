import base64
import codecs
import math
import os
import random
import shutil
from multiprocessing import Pool
import requests
from Crypto.Cipher import AES  # pip install pycrypto


class WangYiYun(object):
    def __init__(self, d):
        self.d = d
        self.e = '010001'
        self.f = "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5a" \
                 "a76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46be" \
                 "e255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7"
        self.g = "0CoJUm6Qyw8W8jud"
        self.random_text = self.get_random_str()

    @staticmethod
    def get_random_str():
        """js中的a函数"""
        string = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        res = ''
        for x in range(16):
            index = math.floor(random.random() * len(string))
            res += string[index]
        return res

    @staticmethod
    def aes_encrypt(text, key):
        iv = '0102030405060708'  # 偏移量
        pad = 16 - len(text.encode()) % 16  # 使加密信息的长度为16的倍数，要不会报下面的错
        # 长度是16的倍数还会报错，不能包含中文，要对他进行unicode编码
        text = text + pad * chr(pad)  # Input strings must be a multiple of 16 in length
        encryptor = AES.new(key, AES.MODE_CBC, iv)
        msg = base64.b64encode(encryptor.encrypt(text))  # 最后还需要使用base64进行加密
        return msg

    @staticmethod
    def rsa_encrypt(value, text, modulus):
        """进行rsa加密"""
        text = text[::-1]
        rs = int(codecs.encode(text.encode('utf-8'), 'hex_codec'), 16) ** int(value, 16) % int(modulus, 16)
        return format(rs, 'x').zfill(256)

    def get_data(self):
        # 这个参数加密两次
        # print(self.d)
        params = self.aes_encrypt(self.d, self.g)
        params = self.aes_encrypt(params.decode('utf-8'), self.random_text)
        # print(params)
        enc_sec_key = self.rsa_encrypt(self.e, self.random_text, self.f)
        # print(enc_sec_key)
        return {
            'params': params,
            'encSecKey': enc_sec_key
        }


class WangYi(object):
    def __init__(self):
        self.music_name_list = self.get_music_names()
        self.download_path = 'music/'
        self.headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
            'Cookie': '_iuqxldmzr_=32; _ntes_nnid=8d4ef0883a3bcc9d3a2889b0bf36766a,1533782432391; _ntes_nuid=8d4ef0883a3bcc9d3a2889b0bf36766a; __utmc=94650624; WM_TID=GzmBlbRkRGQXeQiYuDVCfoEatU6VSsKC; playerid=19729878; __utma=94650624.1180067615.1533782433.1533816989.1533822858.9; __utmz=94650624.1533822858.9.7.utmcsr=cn.bing.com|utmccn=(referral)|utmcmd=referral|utmcct=/; WM_NI=S5gViyNVs14K%2BZoVerGK69gLlmtnH5NqzyHcCUY%2BiWm2ZaHATeI1gfsEnK%2BQ1jyP%2FROzbzDV0AyJHR4YQfBetXSRipyrYCFn%2BNdA%2FA8Mv80riS3cuMVJi%2BAFgCpXTiHBNHE%3D; WM_NIKE=9ca17ae2e6ffcda170e2e6ee84b674afedfbd3cd7d98b8e1d0f554f888a4abc76990b184badc4f89e7af8ece2af0fea7c3b92a91eba9b7ec738e8abdd2b741e986a1b7e87a8595fadae648b0b3bc8fcb3f8eafb69acb69818b97ccec5dafee9682cb4b98bb87d2e66eb19ba2acaa5bf3b6b7b1ae5a8da6ae9bc75ef49fb7abcb5af8879f87c16fb8889db3ec7cbbae97a4c566e992aca2ae4bfc93bad9b37aab8dfd84f8479696a7ccc44ea59dc0b9d7638c9e82a9c837e2a3; JSESSIONID-WYYY=sHwCKYJYxz6ODfURChA471BMF%5CSVf3%5CTc8Qcy9h9Whj6CfMxw4YWTMV7CIx5g6rqW8OBv04YGHwwq%2B%5CD1N61qknTP%2Fym%2BHJZ1ylSH1EabbQASc9ywIT8YvOr%2FpMgvmm1cbr2%2Bd6ssMYXuTlpOIrKqp%5C%2FM611EhmfAfU47%5CSQWAs%2BYzgY%3A1533828139236'
        }

    @staticmethod
    def get_music_names():
        music_names = []
        f = open('./music.txt', 'r', encoding='utf-8')
        lines = f.readlines()
        f.close()
        for line in lines:
            musicname = str(line).strip()
            music_names.append(musicname)
        return music_names

    def __get_mp3(self, musicid):
        d = '{"ids":"[%s]","br":320000,"csrf_token":""}' % musicid
        wyy = WangYiYun(d)
        data = wyy.get_data()
        url = 'https://music.163.com/weapi/song/enhance/player/url?csrf_token='
        response = requests.post(url, data=data, headers=self.headers).json()
        return response['data'][0]['url']

    def download_mp3(self, dwonload_url, filename):
        media_name = 'temp/' + str(filename) + '.mp3'
        open_path = self.download_path + str(filename) + '.mp3'
        if os.path.exists(open_path) is False:
            command_1 = 'ffmpeg -i "%s" -acodec copy -vn "%s"' % (dwonload_url, media_name)
            os.system(command_1)
            size = self.get_size(media_name)
            if size >= 1000000:
                shutil.move(media_name, open_path)
            else:
                os.remove(media_name)
        return

    @staticmethod
    def get_size(file):
        return os.path.getsize(file)

    def existed_file(self, file):
        if os.path.exists(file) is True:
            file = str(file).replace('.mp3', '_2.mp3')
            file = self.existed_file(file)
        return file

    @staticmethod
    def __print_info(songs):
        """打印歌曲需要下载的歌曲信息"""
        songs_list = []
        for num, song in enumerate(songs):
            # print(song)
            # print(num, '歌曲名字：', song['name'], '作者：', song['ar'][0]['name'])
            songs_list.append((song['name'], song['id'], song['ar'][0]['name']))
        return songs_list

    def __get_songs(self, name):
        d = '{"hlpretag":"<span class=\\"s-fc7\\">","hlposttag":"</span>","s":"%s","type":"1","offset":"0",' \
            '"total":"true","limit":"30","csrf_token":""}' % name
        wyy = WangYiYun(d)  # 要搜索的歌曲名在这里
        data = wyy.get_data()
        url = 'https://music.163.com/weapi/cloudsearch/get/web?csrf_token='
        response = requests.post(url, data=data, headers=self.headers).json()
        return response['result']

    def main(self, name):
        songs = self.__get_songs(name)
        if songs['songCount'] == 0:
            print('没有搜到此歌曲，请换个关键字')
        else:
            songs = self.__print_info(songs['songs'])
            if len(songs) > 10:
                songs = songs[:10]
            for song in songs:
                # print(song)
                url = self.__get_mp3(song[1])
                if not url:
                    print('歌曲需要收费，下载失败')
                else:
                    filename = song[2] + '-' + song[0]
                    # print(filename)
                    print(url, filename)
                    self.download_mp3(url, filename)


if __name__ == '__main__':
    app = WangYi()
    p = Pool()
    for music_name in app.music_name_list:
        # app.main(music_name)
        p.apply_async(app.main, (music_name,))
    p.close()
    p.join()
