import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from ast import literal_eval
from sklearn.feature_extraction.text import CountVectorizer


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
m = vote.quantile(0.60)
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
df_metadata = df.iloc[:10000, 6]



#Mapeando a função
mapear = pd.Series(df_metadata.index, index = df.iloc[:10000, 1])



# Funcao de recomendacao de acordo com nossos metadados
def sistema(filmes_input):
    '''list -> list'''
    # "Somando os filmes"
    # indice depende do tamanho do dataframe
    indice = 15468
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
    score = list(enumerate(cosseno_sim_matrix[10000]))
    score = sorted(score, key=lambda x: x[1], reverse=True)

    # Amostra de 10 filmes
    n_filmes = len(filmes_input)
    score = score[(n_filmes + 1):(n_filmes + 11)]
    indices = [i[0] for i in score]

    # Transformando de pd.Series pra lista
    lista_recomendada = mapear.iloc[indices].index.to_list()

    return (lista_recomendada)