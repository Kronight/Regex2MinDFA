# coding: utf-8
from graphviz import Digraph


class NfaNode(object):
    def __init__(self, fromid=None, id=None, toid=None, key=chr(949)):
        self.id = id
        self.key = key
        self.fromid = []
        self.toid = []

        if fromid is None:
            pass
        elif isinstance(fromid, int):
            self.fromid.append(fromid)
        elif isinstance(fromid, list):
            self.fromid = fromid

        if toid is None:
            self.toid = []
        elif isinstance(toid, int):
            if toid not in self.toid:
                self.toid.append(toid)
        elif isinstance(toid, list):
            self.toid = toid

    def __repr__(self):
        return '(from={},is={},to={})'.format(self.fromid, self.id, self.toid)


class DfaNode(object):
    def __init__(self, a_status=None, b_status=None, null_status=None):
        # self.end_status = False
        self.status = {
            'a': [],
            'b': []
        }
        if null_status is not None:
            self.status['a'] = null_status
            self.status['b'] = null_status
        else:
            if a_status is not None:
                self.status['a'] = a_status
            if b_status is not None:
                self.status['b'] = b_status

    def __repr__(self):
        return 'a = {}  b = {}'.format(self.status["a"], self.status["b"])

    def sort(self):
        self.status['a'].sort()
        self.status['b'].sort()


class MDfaNode(object):
    def __init__(self, id_, a, b):
        self.id = id_
        self.a = a
        self.b = b


class Fragment(object):
    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end

    def __repr__(self):
        return '(start={},end={})'.format(self.start.id, self.end.id)


class Token(object):
    def __init__(self):
        self.alphas = ['a', 'b']
        self.operators = ['(', '*', '.', '|', ')']
        self.epsilon = chr(949)  # ε

    def is_alpha(self, char):
        if char in self.alphas:
            return True
        else:
            return False

    def is_operator(self, char):
        if char in self.operators:
            return True
        else:
            return False

    @staticmethod
    def is_left_brackets(char):
        if char == '(':
            return True
        else:
            return False

    @staticmethod
    def is_right_brackets(char):
        if char == ')':
            return True
        else:
            return False


token = Token()
status_index = 0


def modify_regex(old_string):
    new_string = []
    i, length = 1, len(old_string)
    while i < length:
        char = old_string[i]
        front_char = old_string[i - 1]
        new_string.append(front_char)
        if token.is_alpha(front_char) and (token.is_alpha(char) or token.is_left_brackets(char)) is True:
            new_string.append('.')
        elif token.is_right_brackets(front_char) and (token.is_alpha(char) or token.is_left_brackets(char)) is True:
            new_string.append('.')
        elif (token.is_left_brackets(char) or  token.is_alpha(char)) and front_char == '*':
            new_string.append('.')
        i = i + 1
    new_string.append(old_string[length - 1])
    # print(new_string)
    return new_string


def is_prior(char, operator):
    if len(operator) == 0:
        return True
    elif operator[-1] == '(':
        return True
    elif token.operators.index(operator[-1]) > token.operators.index(char):  # 当前元素优先级大于栈顶元素
        return True


def operate(alpha, operator):
    if operator == '*':
        new_alpha = [alpha[-1], operator]
        alpha.pop()
    else:
        new_alpha = [alpha[-2], alpha[-1], operator]
        alpha.pop()
        alpha.pop()
    alpha.append("".join(new_alpha))


def suffixexp(string):
    alpha = []
    operator = []
    new_string = ""
    index, length = 0, len(string)
    while index < length:
        if token.is_alpha(string[index]):
            alpha.append(string[index])
        elif token.is_operator(string[index]):
            if string[index] == '(' or is_prior(string[index], operator):
                operator.append(string[index])
            else:
                while not is_prior(string[index], operator):  # 元素优先级高则直接放入，低则将栈顶运算
                    if string[index] == ')':
                        while len(operator) != 0 and operator[-1] != '(':
                            operate(alpha, operator[-1])
                            operator.pop()
                        if len(operator) != 0:
                            operator.pop()
                        break
                    else:
                        while len(operator) != 0 and operator[-1] != '(' and not is_prior(string[index], operator[-1]):
                            operate(alpha, operator[-1])
                            operator.pop()
                if string[index] != ')':
                    operator.append(string[index])
        index += 1
    while len(alpha) > 1 and len(operator) != 0:
        operate(alpha, operator[-1])
        operator.pop()

    # print(alpha)
    new_string += alpha[0]
    return new_string


def new_alpha_fragment(suffix_string, status):
    global status_index
    status.append(NfaNode(None, status_index, status_index + 1, suffix_string))
    status_index += 1
    status.append(NfaNode(status_index - 1, status_index, None))
    status_index += 1
    return Fragment(start=status[-2], end=status[-1])


def new_operator_fragment(suffix_string, fragments, status):
    global status_index
    if suffix_string == '.':
        fragment_1, fragment_2 = fragments[-2:]
        fragment_1.end.toid.append(fragment_2.start.id)
        fragment_1.end.key = chr(949)
        fragment_2.start.fromid.append(fragment_1.end.id)
        fragments.pop()
        fragments.pop()
        return Fragment(start=fragment_1.start, end=fragment_2.end)
    elif suffix_string == '|':
        fragment_1, fragment_2 = fragments[-2:]
        status.append(
            NfaNode(None, status_index, [fragment.start.id for fragment in fragments[-2:]], chr(949)))  # start
        fragment_1.start.fromid.append(status[-1].id)
        fragment_2.start.fromid.append(status[-1].id)
        status_index += 1
        status.append(
            NfaNode([fragment.end.id for fragment in fragments[-2:]], status_index, None, chr(949)))  # end
        fragment_1.end.toid.append(status[-1].id)
        fragment_2.end.toid.append(status[-1].id)
        status_index += 1
        fragments.pop()
        fragments.pop()
        return Fragment(start=status[-2], end=status[-1])
    elif suffix_string == '*':
        fragment = fragments[-1]
        status.append(NfaNode([fragment.end.id], status_index, None, chr(949)))  # end
        fragment.end.toid.append(status_index)  # back 2 end
        status_index += 1
        status.append(NfaNode(None, status_index, [fragment.start.id, status[-1].id], chr(949)))  # start
        status[-2].fromid.append(status[-1].id)  # start 2 end
        fragment.end.toid.append(fragment.start.id)  # back to front
        fragment.start.fromid.append(fragment.end.id)
        fragment.start.fromid.append(status[-1].id)
        status_index += 1
        fragments.pop()
        return Fragment(start=status[-1], end=status[-2])


def to_nfa(suffix_string):
    nfa_status = []
    nfa_fragments = []
    global status_index
    for index in range(len(suffix_string)):
        if token.is_alpha(suffix_string[index]):
            nfa_fragments.append(new_alpha_fragment(suffix_string[index], nfa_status))
        elif token.is_operator(suffix_string[index]):
            nfa_fragments.append(new_operator_fragment(suffix_string[index], nfa_fragments, nfa_status))
    nfa_status.append(NfaNode(None, status_index, nfa_fragments[-1].start.id, chr(949)))
    nfa_fragments[-1].start = nfa_status[status_index]
    status_index += 1
    return nfa_fragments, nfa_status


def find_null(status, nfa_nodes):
    for index in status:
        if len(nfa_nodes[index].toid) != 0:
            if nfa_nodes[index].key == chr(949):
                for id_add in nfa_nodes[index].toid:
                    find_null([id_add], nfa_nodes)
                    if id_add not in status:
                        status.append(id_add)
    return status


def nfa2dfa(nfa_nodes):
    dfa_nodes = []
    for index in range(len(nfa_nodes)):
        if nfa_nodes[index].toid:
            if nfa_nodes[index].key == chr(949):
                null_status = nfa_nodes[index].toid
                find_null(null_status, nfa_nodes)
                dfa_nodes.append(DfaNode(null_status=null_status))
            else:
                if nfa_nodes[index].key == 'a':
                    a_status = nfa_nodes[index].toid
                    a_status = find_null(a_status, nfa_nodes)
                else:
                    a_status = []
                if nfa_nodes[index].key == 'b':
                    b_status = nfa_nodes[index].toid
                    b_status = find_null(b_status, nfa_nodes)
                else:
                    b_status = []
                dfa_nodes.append(DfaNode(a_status=a_status, b_status=b_status))
        else:
            a_status = None
            b_status = None
            dfa_nodes.append(DfaNode(a_status=a_status, b_status=b_status))
    return dfa_nodes


def dfa_verify(dfa_nodes, start_index, nfa_nodes):
    new_dfa_nodes = []
    list_ = [start_index]
    temp_list = [list_]
    status_set = set()
    status_set.add(tuple(sorted(list_)))
    while temp_list:
        a_temp_list = []
        b_temp_list = []
        for index in temp_list[0]:
            if nfa_nodes[index].key == chr(949):
                for add_id in add_dfa_node(dfa_nodes[index].status['a'], a_temp_list):
                    a_temp_list.append(add_id)
                for add_id in add_dfa_node(dfa_nodes[index].status['b'], b_temp_list):
                    b_temp_list.append(add_id)

            elif nfa_nodes[index].key == 'a':
                for add_id in add_dfa_node(dfa_nodes[index].status['a'], a_temp_list):
                    a_temp_list.append(add_id)
            elif nfa_nodes[index].key == 'b':
                for add_id in add_dfa_node(dfa_nodes[index].status['b'], b_temp_list):
                    b_temp_list.append(add_id)

        a_tuple = tuple(sorted(a_temp_list))
        b_tuple = tuple(sorted(b_temp_list))

        if a_tuple in status_set and b_tuple in status_set:
            break
        else:
            status_set.add(a_tuple)
            status_set.add(b_tuple)
        if a_tuple == b_tuple:
            temp_list.append(a_temp_list)
        else:
            if a_temp_list:
                temp_list.append(a_temp_list)
            if b_temp_list:
                temp_list.append(b_temp_list)
        new_dfa_nodes.append(MDfaNode(tuple(sorted(temp_list[0])), a_tuple, b_tuple))
        del (temp_list[0])
    return new_dfa_nodes, status_set


def add_dfa_node(dfa_node, temp_list):
    result_list = []
    for num in dfa_node:
        if num not in temp_list:
            result_list.append(num)
    return result_list


def dfa_show(end_id, new_dfa_nodes):
    f = Digraph(name="NFA", filename="DFA.gv", format='png')
    f.attr(rankdir='LR', size='8,5')
    f.attr('node', shape='doublecircle')
    for index in range(len(new_dfa_nodes)):
        if end_id in list(new_dfa_nodes[index].id):
            f.node("{}".format(str(new_dfa_nodes[index].id)))
        if end_id in list(new_dfa_nodes[index].a):
            f.node("{}".format(str(new_dfa_nodes[index].a)))
        if end_id in list(new_dfa_nodes[index].b):
            f.node("{}".format(str(new_dfa_nodes[index].b)))
    f.attr('node', shape='circle')
    for index in range(len(new_dfa_nodes)):
        if new_dfa_nodes[index].a:
            f.edge("{}".format(str(new_dfa_nodes[index].id)), "{}".format(str(new_dfa_nodes[index].a)), label="a")
        if new_dfa_nodes[index].b:
            f.edge("{}".format(str(new_dfa_nodes[index].id)), "{}".format(str(new_dfa_nodes[index].b)), label="b")
    # f.view()


def nfa_show(fragments, status):
    f = Digraph(name="NFA", filename="NFA.gv", format='png')
    f.attr(rankdir='LR', size='8,5')
    f.attr('node', shape='doublecircle')
    end_id = fragments[0].end.id
    f.node('{}'.format(str(end_id)))
    f.attr('node', shape='circle')
    for sta in status:
        for to_id in sta.toid:
            f.edge("{}".format(str(sta.id)), "{}".format(str(to_id)), label="{}".format(str(sta.key)))
    # f.view()


def main():
    global token
    global status_index
    # input_string = input('>>')
    input_string = 'b*a(a|b)*'
    # input_string = 'a(a|b)'

    modify_string = "".join(modify_regex(input_string))
    # print(modify_string)

    suffix_string = suffixexp(modify_string)
    # print(suffix_string)
    fragments, nfa_nodes = to_nfa(suffix_string)
    nfa_show(fragments, nfa_nodes)

    dfa_nodes = nfa2dfa(nfa_nodes)
    # print(dfa_nodes)
    start_index = fragments[-1].start.id
    end_index = fragments[-1].end.id

    new_dfa_nodes, status_set = dfa_verify(dfa_nodes, start_index, nfa_nodes)
    # print(new_dfa_nodes)
    dfa_show(end_index, new_dfa_nodes)


if __name__ == '__main__':
    main()
