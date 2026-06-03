def reorder_to_rsl(token_list: list) -> list:
    subjects = []
    objects = []        # прямые дополнения (obj)
    obliques = []       # косвенные дополнения/обстоятельства (obl)
    verbs = []
    modifiers = []      # наречия, отрицания
    adjectives_map = {} # {id_существительного: [прилагательные]}

    for token in token_list:
        if token['upos'] == 'ADJ' and token.get('head') is not None:
            head_id = token['head']
            if head_id not in adjectives_map:
                adjectives_map[head_id] = []
            adjectives_map[head_id].append(token)

    for token in token_list:
        upos = token['upos']
        deprel = token.get('deprel', '')

        # глаголы
        if upos == 'VERB' or (upos == 'AUX' and deprel == 'root'):
            verbs.append(token)

        # подлежащие
        elif deprel == 'nsubj':
            subjects.append(token)

        # прямые дополнения (винительный падеж без предлога)
        elif deprel == 'obj':
            objects.append(token)

        # косвенные дополнения/обстоятельства
        elif deprel == 'obl':
            obliques.append(token)

        # модификаторы (наречия, отрицания)
        elif upos == 'ADV':
            modifiers.append(token)

        elif upos == 'NOUN' and deprel not in ['nsubj', 'obj', 'obl']:
            obliques.append(token)

    def add_with_adjectives(token_list):
        result = []
        for token in token_list:
            result.append(token)
            if token.get('id') in adjectives_map:
                for adj in adjectives_map[token['id']]:
                    result.append(adj)
        return result

    # cобираем в порядке РЖЯ: S + modifiers + O + obliques + V
    # прилагательные добавляем после соответствующих существительных
    result = []
    result.extend(add_with_adjectives(subjects))
    result.extend(modifiers)
    result.extend(add_with_adjectives(objects))
    result.extend(add_with_adjectives(obliques))
    result.extend(verbs)

    return result
