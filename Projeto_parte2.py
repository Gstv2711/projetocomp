#Adicionando sistema de registro de usuários e listas

#Imports para o trailer
import urllib.request
import re
import webbrowser

#Imports para baixar imagem
import requests
from bs4 import BeautifulSoup


class Lista_recomendada:
    '''Classe que contém os filmes curtidos pelo usuário e a lista de filmes recomendados para ele
    None -> None'''
    def __init__(self, filmes_curtidos=[], filmes_recomendados=[]):
        self.filmes_curtidos = filmes_curtidos
        self.filmes_recomendados = filmes_recomendados

    def adicionar_filme_curtido(self, filme_input):
        '''Comando para o botão que adiciona cada filme ao atributo filmes_curtidos
        str -> None'''
        self.filmes_curtidos.append(filme_input)

    def gerar_filmes_recomendados(self):
        '''Método que utiliza o algoritmo principal e printa cada filme recomendado
        None -> None'''
        self.filmes_recomendados = sistema2(filmes_curtidos)
        for filme in self.filmes_recomendados:
            print(filme)

    def mostrar_trailer(self):
        '''Método de mostrar trailer do filme
        None -> None'''
        filme = self.filmes_recomendados[0].replace(' ', '+') + '+movie+trailer'
        html = urllib.request.urlopen('https://www.youtube.com/results?search_query=' + filme)
        video_ids = re.findall(r'watch\?v=(\S{11})', html.read().decode())
        webbrowser.open('https://www.youtube.com/watch?v=' + video_ids[0])

    def baixar_imagem(self):
        '''Método para gerar imagens para os filmes recomendados
        None -> None'''
        for filme in self.filmes_recomendados:
            nome = filme + ' movie poster'
            url = 'https://www.google.com/search?q=' + nome + '&tbm=isch'
            r = requests.get(url)
            soup = BeautifulSoup(r.text, 'html.parser')
            imagens = soup.find_all('img')
            imagem = imagens[1]
            link = imagem['src']
            with open(nome + '.jpg', 'wb') as f:
                im = requests.get(link)
                f.write(im.content)


class Usuario:
    '''Classe que armazena as informações de cada usuário'''
    def __init__(self, nome, listas_recomendadas=[]):
        self.nome = nome
        self.listas_recomendadas = listas_recomendadas

    def add_lista(self, lista_recomendada):
        '''Método de adicionar lista recomendada
        list[str] -> None'''
        self.listas_recomendadas.append(lista_recomendada)


#exemplos:
#user1 = Usuario('Gustavo')
#lista1 = Lista_recomendada()
#lista1.adicionar_filme_curtido(filme_input)

