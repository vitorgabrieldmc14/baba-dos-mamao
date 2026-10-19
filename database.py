import sqlite3
import json
from datetime import datetime, timedelta


def iniciar_banco():
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jogadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            whatsapp TEXT UNIQUE,
            senha TEXT,
            posicao TEXT,
            pontos_fortes TEXT,
            pontos_fracos TEXT,
            nota_media REAL DEFAULT 6.0,
            perfil TEXT DEFAULT 'JOGADOR'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS partidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_partida TEXT,
            local TEXT,
            status TEXT DEFAULT 'ABERTA'
        )
    ''')
    try:
        cursor.execute("ALTER TABLE partidas ADD COLUMN hora_partida TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE partidas ADD COLUMN times_sorteados TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE partidas ADD COLUMN time_campeao TEXT")
    except:
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS presencas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partida_id INTEGER,
            jogador_id INTEGER, 
            nome_convidado TEXT,
            nota_convidado INTEGER
        )
    ''')
    try:
        cursor.execute("ALTER TABLE presencas ADD COLUMN posicao_convidado TEXT")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE presencas ADD COLUMN gols INTEGER DEFAULT 0")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE presencas ADD COLUMN assistencias INTEGER DEFAULT 0")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE presencas ADD COLUMN baliza_zero INTEGER DEFAULT 0")
    except:
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS avaliacoes (
            partida_id INTEGER,
            avaliador_id INTEGER,
            avaliado_presenca_id INTEGER,
            nota INTEGER
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS votos_craque (
            partida_id INTEGER,
            eleitor_id INTEGER,
            escolhido_presenca_id INTEGER
        )
    ''')
    conn.commit()
    conn.close()


def salvar_jogador(nome, whatsapp, senha, posicao, fortes, fracos):
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO jogadores (nome, whatsapp, senha, posicao, pontos_fortes, pontos_fracos) VALUES (?, ?, ?, ?, ?, ?)',
            (nome, whatsapp, senha, posicao, ", ".join(fortes), ", ".join(fracos)))
        conn.commit()
        sucesso = True
    except sqlite3.IntegrityError:
        sucesso = False
    conn.close()
    return sucesso


def verificar_login(whatsapp, senha):
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome, perfil, whatsapp FROM jogadores WHERE whatsapp=? AND senha=?', (whatsapp, senha))
    usuario = cursor.fetchone()
    conn.close()
    return usuario


def alterar_perfil(id_jogador, novo_perfil):
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE jogadores SET perfil = ? WHERE id = ?", (novo_perfil, id_jogador))
    conn.commit()
    conn.close()


def excluir_jogador(id_jogador):
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jogadores WHERE id = ?", (id_jogador,))
    cursor.execute("DELETE FROM presencas WHERE jogador_id = ?", (id_jogador,))
    conn.commit()
    conn.close()


# --- NOVA FUNÇÃO: DIRETORIA ALTERAR NOTA MANUALMENTE ---
def atualizar_nota_jogador(jogador_id, nova_nota):
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE jogadores SET nota_media = ? WHERE id = ?", (nova_nota, jogador_id))
    conn.commit()
    conn.close()


def criar_partida(data, hora, local):
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE partidas SET status = 'ENCERRADA' WHERE status IN ('ABERTA', 'FECHADA', 'EM AVALIAÇÃO')")
    cursor.execute("INSERT INTO partidas (data_partida, hora_partida, local, status) VALUES (?, ?, ?, 'ABERTA')",
                   (str(data), str(hora), local))
    conn.commit()
    conn.close()


def obter_partida_ativa():
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, data_partida, local, IFNULL(hora_partida, 'A definir'), status, times_sorteados FROM partidas WHERE status IN ('ABERTA', 'FECHADA', 'EM AVALIAÇÃO') LIMIT 1")
    partida = cursor.fetchone()
    conn.close()
    return partida


def alterar_status_partida(partida_id, novo_status):
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE partidas SET status = ? WHERE id = ?", (novo_status, partida_id))
    conn.commit()
    conn.close()


def checar_limite_21(partida_id):
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM presencas WHERE partida_id=?", (partida_id,))
    total = cursor.fetchone()[0]
    conn.close()
    return total >= 21


def confirmar_presenca(partida_id, jogador_id):
    if checar_limite_21(partida_id): return False
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM presencas WHERE partida_id=? AND jogador_id=?", (partida_id, jogador_id))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO presencas (partida_id, jogador_id) VALUES (?, ?)", (partida_id, jogador_id))
        conn.commit()
    conn.close()
    return True


def adicionar_convidado(partida_id, nome, nota, posicao):
    if checar_limite_21(partida_id): return False
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO presencas (partida_id, nome_convidado, nota_convidado, posicao_convidado) VALUES (?, ?, ?, ?)",
        (partida_id, nome, nota, posicao))
    conn.commit()
    conn.close()
    return True


def obter_lista_presenca(partida_id):
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, j.nome, 'Fixo' as tipo, j.nota_media, j.posicao, j.id as j_id, p.gols, p.assistencias, p.baliza_zero
        FROM presencas p 
        JOIN jogadores j ON p.jogador_id = j.id 
        WHERE p.partida_id = ?
        UNION ALL
        SELECT id, nome_convidado as nome, 'Convidado' as tipo, nota_convidado as nota_media, IFNULL(posicao_convidado, 'Não informada') as posicao, NULL as j_id, gols, assistencias, baliza_zero
        FROM presencas 
        WHERE partida_id = ? AND jogador_id IS NULL
    ''', (partida_id, partida_id))
    lista = cursor.fetchall()
    conn.close()
    return lista


def remover_presenca(partida_id, jogador_id):
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM presencas WHERE partida_id=? AND jogador_id=?", (partida_id, jogador_id))
    conn.commit()
    conn.close()


def remover_convidado_bd(presenca_id):
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM presencas WHERE id=?", (presenca_id,))
    conn.commit()
    conn.close()


def verificar_limite_horario(data_partida_str, hora_partida_str):
    agora = datetime.now()
    if not hora_partida_str or hora_partida_str == 'A definir':
        return True
    try:
        data_hora_jogo_str = f"{data_partida_str} {hora_partida_str}"
        data_hora_jogo = datetime.strptime(data_hora_jogo_str, '%Y-%m-%d %H:%M')
        limite = data_hora_jogo - timedelta(hours=1)
        return agora < limite
    except:
        return True


def formatar_whatsapp(numero_digitado):
    numeros = ''.join(filter(str.isdigit, numero_digitado))
    if len(numeros) == 11: return f"+55 {numeros[:2]} {numeros[2:7]}-{numeros[7:]}"
    return numeros


def obter_colegas_equipe(partida_id, meu_jogador_id):
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute("SELECT times_sorteados FROM partidas WHERE id=?", (partida_id,))
    row = cursor.fetchone()
    conn.close()
    if not row or not row[0]: return []

    dados_sorteio = json.loads(row[0])
    times = dados_sorteio['times']
    goleiros_fixos = dados_sorteio.get('goleiros_fixos', False)
    lista_goleiros = dados_sorteio.get('lista_goleiros', [])

    meu_time = []
    eh_goleiro_fixo = False

    if goleiros_fixos and any(g[5] == meu_jogador_id for g in lista_goleiros):
        eh_goleiro_fixo = True

    for nome_time, elenco in times.items():
        todos_do_time = elenco['Goleiros'] + elenco['Titulares'] + elenco['Reservas']
        if any(j[5] == meu_jogador_id for j in todos_do_time):
            meu_time.extend(todos_do_time)

    colegas = [j for j in meu_time if j[5] != meu_jogador_id]

    if goleiros_fixos:
        for gol in lista_goleiros:
            if gol[5] != meu_jogador_id and gol not in colegas:
                colegas.append(gol)

        if eh_goleiro_fixo:
            for nome_time, elenco in times.items():
                todos_linha = elenco['Titulares'] + elenco['Reservas']
                for j in todos_linha:
                    if j[5] != meu_jogador_id and j not in colegas:
                        colegas.append(j)

    colegas_unicos = []
    ids_vistos = set()
    for c in colegas:
        if c[0] not in ids_vistos:
            ids_vistos.add(c[0])
            colegas_unicos.append(c)

    return colegas_unicos


def salvar_avaliacoes(partida_id, avaliador_id, notas_dict, craque_presenca_id):
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM avaliacoes WHERE partida_id=? AND avaliador_id=?", (partida_id, avaliador_id))
    cursor.execute("DELETE FROM votos_craque WHERE partida_id=? AND eleitor_id=?", (partida_id, avaliador_id))

    for avaliado_presenca_id, nota in notas_dict.items():
        cursor.execute(
            "INSERT INTO avaliacoes (partida_id, avaliador_id, avaliado_presenca_id, nota) VALUES (?, ?, ?, ?)",
            (partida_id, avaliador_id, avaliado_presenca_id, nota))

    if craque_presenca_id:
        cursor.execute("INSERT INTO votos_craque (partida_id, eleitor_id, escolhido_presenca_id) VALUES (?, ?, ?)",
                       (partida_id, avaliador_id, craque_presenca_id))
    conn.commit()
    conn.close()


def verificar_ja_votou(partida_id, avaliador_id):
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM avaliacoes WHERE partida_id=? AND avaliador_id=?", (partida_id, avaliador_id))
    votou = cursor.fetchone() is not None
    conn.close()
    return votou


# --- ATUALIZADO: MÉDIA BASEADA APENAS NAS ÚLTIMAS 5 PARTIDAS ---
def encerrar_partida_definitivamente(partida_id, time_campeao):
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()

    # Seleciona todo mundo que participou e recebeu notas nesse baba
    cursor.execute('''
        SELECT DISTINCT p.jogador_id 
        FROM avaliacoes a
        JOIN presencas p ON a.avaliado_presenca_id = p.id
        WHERE a.partida_id = ? AND p.jogador_id IS NOT NULL
    ''', (partida_id,))
    jogadores_avaliados = cursor.fetchall()

    for (jogador_id,) in jogadores_avaliados:
        # Puxa a média agrupando apenas os últimos 5 babas que ESSE jogador esteve presente e recebeu nota
        cursor.execute('''
            SELECT AVG(a.nota) 
            FROM avaliacoes a
            JOIN presencas p ON a.avaliado_presenca_id = p.id
            WHERE p.jogador_id = ? AND a.partida_id IN (
                SELECT DISTINCT a2.partida_id 
                FROM avaliacoes a2
                JOIN presencas p2 ON a2.avaliado_presenca_id = p2.id
                WHERE p2.jogador_id = ?
                ORDER BY a2.partida_id DESC
                LIMIT 5
            )
        ''', (jogador_id, jogador_id))
        media_ultimas_5 = cursor.fetchone()[0]

        if media_ultimas_5 is not None:
            cursor.execute("UPDATE jogadores SET nota_media = ? WHERE id = ?", (round(media_ultimas_5, 1), jogador_id))

    cursor.execute("UPDATE partidas SET status = 'ENCERRADA', time_campeao = ? WHERE id = ?",
                   (time_campeao, partida_id))
    conn.commit()
    conn.close()


def salvar_sorteio_oficial(partida_id, json_str):
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE partidas SET times_sorteados = ? WHERE id = ?", (json_str, partida_id))
    conn.commit()
    conn.close()


def obter_ultimo_campeao():
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT data_partida, time_campeao, times_sorteados 
        FROM partidas 
        WHERE status = 'ENCERRADA' AND time_campeao IS NOT NULL AND time_campeao != 'Nenhum / Empate'
        ORDER BY id DESC LIMIT 1
    ''')
    row = cursor.fetchone()
    conn.close()
    return row


def obter_top5_estatistica(campo):
    conn = sqlite3.connect('pelada.db')
    cursor = conn.cursor()
    query = f'''
        SELECT j.nome, SUM(p.{campo}) as total 
        FROM presencas p 
        JOIN jogadores j ON p.jogador_id = j.id
        GROUP BY j.id 
        HAVING total > 0 
        ORDER BY total DESC, j.nome ASC 
        LIMIT 5
    '''
    cursor.execute(query)
    res = cursor.fetchall()
    conn.close()
    return res