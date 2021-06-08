#Imports do algorítmo
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from ast import literal_eval
from sklearn.feature_extraction.text import CountVectorizer

#Imports para o trailer
import urllib.request
import re
import webbrowser

#Imports para baixar imagem
import requests
from bs4 import BeautifulSoup

#Import para a interface
from tkinter import *
from PIL import ImageTk,Image



filmes = pd.read_csv("movies_metadata.csv")
creditos = pd.read_csv("credits.csv")
palavraschaves = pd.read_csv("keywords.csv")

filmes = filmes[["id", "title", "genres","vote_average", "vote_count"]]


#Função de limpar os ID's
def limpa_id(x):
    try:
        return int(x)

    except:
        return np.nan


filmes['id'] = filmes['id'].apply(limpa_id)
filmes = filmes[filmes['id'].notnull()]

filmes['id'] = filmes['id'].astype('int')
palavraschaves['id'] = palavraschaves['id']
creditos['id'] = creditos['id'].astype('int')


# Juntando através do id
filmes1 = filmes.merge(creditos, on="id")
filmes2 = filmes1.merge(palavraschaves, on="id")


# Aplicando literal_eval para fazer string -> objetos.
filmes2['genres'] = filmes2['genres'].apply(literal_eval)
filmes2['cast'] = filmes2['cast'].apply(literal_eval)
filmes2['crew'] = filmes2['crew'].apply(literal_eval)
filmes2['keywords'] = filmes2['keywords'].apply(literal_eval)


# Pegando o nome dos diretores associados
filmes2['crew'] = filmes2['crew'].apply(lambda x: [i['name'].lower() for i in x if i['job'] == 'Director'])


df = filmes2


#Aplicando filtro de filmes mais relevantes
vote = df[df["vote_count"].notnull()]["vote_count"].astype('float')
avg = df[df["vote_average"].notnull()]["vote_average"].astype('float')
C = avg.mean()
m = vote.quantile(0.70)
qualified = df[(df['vote_count'] >= m) & (df['vote_count'].notnull()) & (df['vote_average'].notnull())]


def imdb_qualified(x):
    v = x["vote_count"]
    R = x["vote_average"]
    return (v/(v+m) * R) + (m/(m+v) * C)

qualified['wr'] = qualified.apply(imdb_qualified, axis = 1)
df = qualified[["id", "title", "genres", "cast", "crew", "keywords"]]


# Colocando tudo em letra minúscula
df["genres"] = df["genres"].apply(lambda x: [i["name"].lower() for i in x])
df["cast"] = df["cast"].apply(lambda x: [i["name"].lower() for i in x])
df["keywords"] = df["keywords"].apply(lambda x: [i["name"].lower() for i in x])


# Pegando até 3 caracteristicas de cada filme
# Se pegarmos muitas caracteristicas pode aumentar demais a complexidade do algortimo
df["genres"] = df["genres"].apply(lambda x: x[:3] if len(x)>3 else x)
df["cast"] = df["cast"].apply(lambda x: x[:3] if len(x)>3 else x)
df["keywords"] = df["keywords"].apply(lambda x: x[:3] if len(x)>3 else x)


#Removendo os espaços
df["cast"] = df["cast"].apply(lambda x: [i.replace(" ","") for i in x])
df["crew"] = df["crew"].apply(lambda x: [i.replace(" ","") for i in x])
df["keywords"] = df["keywords"].apply(lambda x: [i.replace(" ","") for i in x])
df["genres"] = df["genres"].apply(lambda x: [i.replace(" ","") for i in x])


#Removendo filmes com nomes repetidos
df = df.drop_duplicates(subset='title', keep='first')


#Transformando tudo em uma coluna só
df["metadata"] = df.apply(lambda x : " ".join(x["genres"]) + " "  + " ".join(x["cast"]) + " " + " ".join(x["crew"]) + " " + " ".join(x["keywords"]), axis = 1)
df_metadata = df.iloc[:13267, 6]


#Mapeando a função
mapear = pd.Series(df_metadata.index, index = df.iloc[:13267, 1])


# Funcao de recomendacao de acordo com nossos metadados
def sistema(filmes_input):
    ''' Função de recomendação de filmes
    list[str] -> list'''
    # "Somando os filmes"
    # indice depende do tamanho do dataframe
    indice = 13268
    df_metadata[indice] = ' '
    for filme in filmes_input:
        df_metadata[indice] += ' ' + df_metadata[mapear[filme]]

    # Usando a similaridade de cosseno
    cv = CountVectorizer(stop_words='english')
    contador_matrix = cv.fit_transform(df_metadata)
    cosseno_sim_matrix = cosine_similarity(contador_matrix)

    # Resetando a soma de filmes
    df_metadata[indice] = ' '

    # Obtendo os valores similares
    score = list(enumerate(cosseno_sim_matrix[13267]))
    score = sorted(score, key=lambda x: x[1], reverse=True)

    # Amostra de 10 filmes
    n_filmes = len(filmes_input)
    score = score[(n_filmes + 1):(n_filmes + 11)]
    indices = [i[0] for i in score]

    # Transformando de pd.Series pra lista
    lista_recomendada = mapear.iloc[indices].index.to_list()

    return (lista_recomendada)



#Adicionando sistema de registro de usuários e listas
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
        self.filmes_recomendados = sistema(self.filmes_curtidos)

    def baixar_imagem(self):
        '''Método para gerar imagens para os filmes recomendados
        None -> None'''
        filme = self.filmes_recomendados[0]
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



#Criando a interface do programa:
inicio = Tk()
inicio.title('GULUMA')
inicio.iconbitmap(r'GULUMA_icone.ico')
l = 800
h = 700
l_tela = inicio.winfo_screenwidth()
h_tela = inicio.winfo_screenheight()
inicio.geometry(str.format('{}x{}+{}+{}',l,h,int(l_tela/2-l/2),int(h_tela/2-(h/2+30))))
inicio['bg']='black'
bvindo = Label(inicio,text='BEM VINDO AO',font='Britannic 15',bg='black',fg='white').place(x=l/2,y=(h/2)-150,anchor='center')
guluma = Label(inicio,text='GULUMA',font='Algerian 85 bold',bg='black',fg='red',height=1).place(x=l/2,y=(h/2)-50,anchor='center')
sub = Label(inicio,text='Seu novo sistema de recomendação de filmes!',font='Britannic 15',bg='black',fg='white').place(x=l/2,y=(h/2)+50,anchor='center')
insiranome = Label(inicio,text='Insira seu nome:',font='Britannic 15',bg='black',fg='white').place(x=l/2,y=(h/2)+110,anchor='center')
nomeuser = Entry(inicio,font='Britannic 15',width=10)
nomeuser.place(x=l/2-20,y=h/2+150,anchor='center')

def comandoOK(event=None):
    '''Comando que continua o programa (muda para a página 2).'''
    if nomeuser.get() == '' or nomeuser.get() == ' ':
        erronome = Label(inicio, text='Insira um nome válido no espaço acima indicado.', font='Britannic 15', bg='black',fg='red').place(x=l / 2, y=h / 2 + 190, anchor='center')

    else:
        user = Usuario(nomeuser.get())
        inicio.destroy()
        tela2 = Tk()
        tela2.title('GULUMA')
        tela2.iconbitmap(r'GULUMA_icone.ico')
        tela2.geometry(str.format('{}x{}+{}+{}',l,h,int(l_tela/2-l/2),int(h_tela/2-(h/2+30))))
        tela2['bg'] = 'black'
        guluma = Label(tela2, text='GULUMA', font='Algerian 85 bold', bg='black', fg='red', height=1).place(x=l / 2,y=(h / 2) - 280,anchor='center')
        listalabel = Label(tela2,text=str.format('Lista de {}:',user.nome),font='Britannic 15 underline',bg='black',fg='white').place(x=l /2-200, y=h/2-190,anchor='center')
        listauser = Lista_recomendada()
        top = Label(tela2,text='Top 6 Filmes:',font='Britannic 15 underline',bg='black',fg='white').place(x=l /2+180, y=h/2-190,anchor='center')


        def conferir_lista():
            '''Função que confere a lista de filmes curtidos'''
            if listauser.filmes_curtidos == []:
                global vazia
                vazia = Label(tela2,text='Nenhum filme na lista.',font='Britannic 10',bg='black',fg='gray')
                vazia.place(x=l /2-200,y=h/2-150,anchor='center')
                global adc
                adc = Label(tela2,text='Acicione dos recomendados ou pesquise!',font='Britannic 10',bg='black',fg='gray')
                adc.place(x=l /2-200,y=h/2-130,anchor='center')

            else:
                for filme in range(len(listauser.filmes_curtidos)):
                    curtido = Label(tela2,text=str.format('{}. {}',filme+1,listauser.filmes_curtidos[filme]),font='Britannic 12',bg='black',fg='white')
                    curtido.place(x=l /2-200,y=h/2-150+filme*30,anchor='center')
                vazia.destroy()
                adc.destroy()

        conferir_lista()

        def comandopesquisa():
            '''Comando ligado ao botão de pesquisa, que abre a aba de pesquisa'''
            pesquisa.destroy()
            nomefilme = Label(tela2,text='Digite o filme de seu interesse:',font='Britannic 12',bg='black',fg='white')
            nomefilme.place(x=l/2+200,y=(h/2)+200,anchor='center')
            barra = Entry(tela2, font='Britannic 15', width=15)
            barra.place(x=l /2+180, y=h/2+235,anchor='center')


            def comandoinserir():
                '''Comando do botão + (inserir), que insere o filme na lista de curtidos'''
                if barra.get() in listauser.filmes_curtidos:
                    global ja_adc
                    ja_adc = Label(tela2, text='O filme escolhido já foi adicionado.', font='Britannic 10', bg='black',fg='red')
                    ja_adc.place(x=l / 2 + 200, y=h / 2 + 180, anchor='center')

                elif barra.get() not in listafilmes:
                    global fora
                    fora = Label(tela2, text='O filme escolhido não existe na lista.', font='Britannic 10', bg='black',
                                 fg='red')
                    fora.place(x=l / 2 + 200, y=h / 2 + 180, anchor='center')

                else:
                    if 'ja_adc' in globals():
                        ja_adc.destroy()

                    if 'fora' in globals():
                        fora.destroy()

                    if barra.get() in listafilmes:
                        listauser.adicionar_filme_curtido(barra.get())
                        barra.delete(0,END)
                        conferir_lista()


            #Define o botão inserir e a listbox:
            inserir = Button(tela2, text='+', font='Britannic 8 bold', command=comandoinserir)
            inserir.place(x=l / 2 + 290, y=(h / 2) +235, anchor='center')
            filmbox = Listbox(tela2, width=28,height=4)
            filmbox.place(x=l / 2 + 180, y=h / 2 +300 , anchor='center')

            def comandoatualizar(elementos):
                '''Função que atualiza a Listbox de acordo com a barra de pesquisa.'''
                filmbox.delete(0,END)
                for elemento in elementos:
                    filmbox.insert(END,elemento)


            listafilmes = mapear.iloc[:].index.to_list()
            comandoatualizar(listafilmes)


            def comandoselecionar(event):
                '''Comando que seleciona o filme pesquisado no resultado da listbox'''
                barra.delete(0,END)
                barra.insert(0,filmbox.get(ACTIVE))

            def comandoopcao(event):
                '''Comando que mostra a listbox de acordo com a pesquisa'''
                digitado = barra.get()
                if digitado == '':
                    elementos = listafilmes
                else:
                    elementos = []
                    for x in listafilmes:
                        if digitado.lower() in x.lower():
                            elementos.append(x)
                comandoatualizar(elementos)


            #Define os comandos da listbox:
            filmbox.bind('<<ListboxSelect>>',comandoselecionar)
            barra.bind('<KeyRelease>',comandoopcao)

        def comandoinserirtop(nome):
            '''Comando ao clicar um filme do TOP 6 (inserir), que insere o filme na lista de curtidos'''
            if nome in listauser.filmes_curtidos:
                global ja_adc
                ja_adc = Label(tela2, text='O filme escolhido já foi adicionado.', font='Britannic 10', bg='black',fg='red')
                ja_adc.place(x=l / 2 + 200, y=h / 2 + 180, anchor='center')

            else:
                if 'ja_adc' in globals():
                    ja_adc.destroy()
                    listauser.adicionar_filme_curtido(nome)
                    conferir_lista()

                else:
                    listauser.adicionar_filme_curtido(nome)
                    conferir_lista()

        #Adicionando os top 6 filmes mais relevantes
        global img_shawshank
        img_shawshank = ImageTk.PhotoImage(Image.open('The Shawshank Redemption movie poster.jpg'))
        f1 = Label(tela2, image=img_shawshank,cursor='hand2')
        f1.place(x=l / 2 + 50, y=h / 2 - 80, anchor='center')
        f1.bind("<Button-1>", lambda e: comandoinserirtop('The Shawshank Redemption'))

        global img_poderoso
        img_poderoso = ImageTk.PhotoImage(Image.open('The Godfather movie poster.jpg'))
        f2 = Label(tela2, image=img_poderoso,cursor='hand2')
        f2.place(x=l / 2 + 180, y=h / 2 - 80, anchor='center')
        f2.bind("<Button-1>", lambda e: comandoinserirtop('The Godfather'))

        global img_schindler
        img_schindler = ImageTk.PhotoImage(Image.open("Schindler's List movie poster.jpg"))
        f3 = Label(tela2, image=img_schindler,cursor='hand2')
        f3.place(x=l / 2 + 310, y=h / 2 - 80, anchor='center')
        f3.bind("<Button-1>", lambda e: comandoinserirtop("Schindler's List"))

        global img_batman
        img_batman = ImageTk.PhotoImage(Image.open('The Dark Knight movie poster.jpg'))
        f4 = Label(tela2, image=img_batman,cursor='hand2')
        f4.place(x=l / 2 + 50, y=h / 2 + 90, anchor='center')
        f4.bind("<Button-1>", lambda e: comandoinserirtop('The Dark Knight'))

        global img_clube
        img_clube = ImageTk.PhotoImage(Image.open('Fight Club movie poster.jpg'))
        f5 = Label(tela2, image=img_clube,cursor='hand2')
        f5.place(x=l / 2 + 180, y=h / 2 + 90, anchor='center')
        f5.bind("<Button-1>", lambda e: comandoinserirtop('Fight Club'))

        global img_pulp
        img_pulp = ImageTk.PhotoImage(Image.open('Pulp Fiction movie poster.jpg'))
        f6 = Label(tela2, image=img_pulp,cursor='hand2')
        f6.place(x=l / 2 + 310, y=h / 2 + 90, anchor='center')
        f6.bind("<Button-1>", lambda e: comandoinserirtop('Pulp Fiction'))

        def comandorecomendar():
            '''Comando do botão de recomendação (para passar para a última página e rodar o algoritmo de recomendação'''
            if listauser.filmes_curtidos == []:
                listavazia = Label(tela2, text='Sua lista de filmes ainda está vazia.', font='Britannic 10', bg='black',fg='red')
                listavazia.place(x=l / 2-200, y=h / 2 + 250, anchor='center')

            else:
                carregando = Label(tela2, text='Carregando...', font='Britannic 10', bg='black',fg='gray')
                carregando.place(x=l / 2 - 200, y=h / 2 + 250, anchor='center')
                listauser.gerar_filmes_recomendados()
                listauser.baixar_imagem()
                tela2.destroy()
                tela3 = Tk()
                tela3.title('GULUMA')
                tela3.iconbitmap(r'GULUMA_icone.ico')
                tela3.geometry(str.format('{}x{}+{}+{}',l,h,int(l_tela/2-l/2),int(h_tela/2-(h/2+30))))
                tela3['bg'] = 'black'
                guluma = Label(tela3, text='GULUMA', font='Algerian 85 bold', bg='black', fg='red', height=1).place(x=l / 2, y=(h / 2) - 280, anchor='center')
                listalabel = Label(tela3, text=str.format('Lista de {}:', user.nome), font='Britannic 15 underline',bg='black', fg='white').place(x=l / 2 - 200, y=h / 2 - 190, anchor='center')
                for filme in range(len(listauser.filmes_curtidos)):
                    curtido = Label(tela3,text=str.format('{}. {}',filme+1,listauser.filmes_curtidos[filme]),font='Britannic 12',bg='black',fg='white')
                    curtido.place(x=l /2-200,y=h/2-150+filme*30,anchor='center')

                equipe = Label(tela3, text='Equipe GULUMA:', font='Algerian 18 bold underline', bg='black', fg='red', height=1).place(x=l / 2-200, y=(h / 2) +200, anchor='center')
                gustavo = Label(tela3, text='GUSTAVO DIAS', font='Algerian 15 bold', bg='black', fg='red', height=1).place(x=l / 2-200, y=(h / 2) +230, anchor='center')
                lucas = Label(tela3, text='LUCAS SOUZA', font='Algerian 15 bold', bg='black', fg='red', height=1).place(x=l / 2-200, y=(h / 2) +260, anchor='center')
                manoel = Label(tela3, text='MANOEL FERNANDES', font='Algerian 15 bold', bg='black', fg='red', height=1).place(x=l / 2-200, y=(h / 2) +290, anchor='center')

                recomlabel = Label(tela3, text='Lista recomendada:', font='Britannic 15 underline',bg='black', fg='white').place(x=l / 2 + 200, y=h / 2-190,anchor='center')

                def comandotrailer(filme):
                    '''Função que cria um link para cada filme recomendado'''
                    nomefilme = listauser.filmes_recomendados[filme].replace(' ', '+') + '+movie+trailer'
                    html = urllib.request.urlopen('https://www.youtube.com/results?search_query=' + nomefilme)
                    video_ids = re.findall(r'watch\?v=(\S{11})', html.read().decode())
                    webbrowser.open_new(('https://www.youtube.com/watch?v=' + video_ids[0]))

                #Adicionando a lista de filmes recomendados
                global img_recomendado1
                img_recomendado1 = ImageTk.PhotoImage(Image.open(str.format('{} movie poster.jpg',listauser.filmes_recomendados[0])))
                cartaz1 = Label(tela3, image=img_recomendado1)
                cartaz1.place(x=l / 2 + 200, y=h / 2 - 80, anchor='center')
                recomendado1 = Label(tela3,text=str.format('{}. {}',1,listauser.filmes_recomendados[0]),font='Britannic 12',bg='black',fg='white',cursor='hand2')
                recomendado1.place(x=l /2+200,y=h/2+15,anchor='center')
                recomendado1.bind("<Button-1>",lambda e: comandotrailer(0))

                recomendado2 = Label(tela3, text=str.format('{}. {}', 2, listauser.filmes_recomendados[1]),font='Britannic 12', bg='black', fg='white', cursor='hand2')
                recomendado2.place(x=l / 2 + 200, y=h / 2+60, anchor='center')
                recomendado2.bind("<Button-1>", lambda e: comandotrailer(1))

                recomendado3 = Label(tela3, text=str.format('{}. {}', 3, listauser.filmes_recomendados[2]),font='Britannic 12', bg='black', fg='white', cursor='hand2')
                recomendado3.place(x=l / 2 + 200, y=h / 2 +90, anchor='center')
                recomendado3.bind("<Button-1>", lambda e: comandotrailer(2))

                recomendado4 = Label(tela3, text=str.format('{}. {}', 4, listauser.filmes_recomendados[3]),font='Britannic 12', bg='black', fg='white', cursor='hand2')
                recomendado4.place(x=l / 2 + 200, y=h / 2 +120, anchor='center')
                recomendado4.bind("<Button-1>", lambda e: comandotrailer(3))

                recomendado5 = Label(tela3, text=str.format('{}. {}', 5, listauser.filmes_recomendados[4]),font='Britannic 12', bg='black', fg='white', cursor='hand2')
                recomendado5.place(x=l / 2 + 200, y=h / 2 +150, anchor='center')
                recomendado5.bind("<Button-1>", lambda e: comandotrailer(4))

                recomendado6 = Label(tela3, text=str.format('{}. {}', 6, listauser.filmes_recomendados[5]),font='Britannic 12', bg='black', fg='white', cursor='hand2')
                recomendado6.place(x=l / 2 + 200, y=h / 2 + 180, anchor='center')
                recomendado6.bind("<Button-1>", lambda e: comandotrailer(5))

                recomendado7 = Label(tela3, text=str.format('{}. {}', 7, listauser.filmes_recomendados[6]),font='Britannic 12', bg='black', fg='white', cursor='hand2')
                recomendado7.place(x=l / 2 + 200, y=h / 2 +210, anchor='center')
                recomendado7.bind("<Button-1>", lambda e: comandotrailer(6))

                recomendado8 = Label(tela3, text=str.format('{}. {}', 8, listauser.filmes_recomendados[7]),font='Britannic 12', bg='black', fg='white', cursor='hand2')
                recomendado8.place(x=l / 2 + 200, y=h / 2 +240, anchor='center')
                recomendado8.bind("<Button-1>", lambda e: comandotrailer(7))

                recomendado9 = Label(tela3, text=str.format('{}. {}', 9,listauser.filmes_recomendados[8]),font='Britannic 12', bg='black', fg='white', cursor='hand2')
                recomendado9.place(x=l / 2 + 200, y=h / 2 +270, anchor='center')
                recomendado9.bind("<Button-1>", lambda e: comandotrailer(8))

                recomendado10 = Label(tela3, text=str.format('{}. {}', 10,listauser.filmes_recomendados[9]),font='Britannic 12', bg='black', fg='white', cursor='hand2')
                recomendado10.place(x=l / 2 + 200, y=h / 2 +300, anchor='center')
                recomendado10.bind("<Button-1>", lambda e: comandotrailer(9))

        #Define os botões de pesquisa e recomendação da página 2:
        pesquisa = Button(tela2,text='Pesquisar',font='Britannic 12 bold',command=comandopesquisa)
        pesquisa.place(x=l /2+180, y=h/2+220,anchor='center')
        recomende = Button(tela2,text='Recomende-me filmes!',font='Britannic 12 bold',command=comandorecomendar)
        recomende.place(x=l /2-200,y=h/2+220,anchor='center')


#Define o botão e o comando ao pressionar enter na primeira página:
ok = Button(inicio,text='OK',font='Britannic 8 bold',command=comandoOK).place(x=l/2+60,y=h/2+150,anchor='center')
inicio.bind('<Return>', comandoOK)


inicio.mainloop()
