# coding: utf-8
from graphviz import Digraph


class NfaNode(object):
    def __init__(self, fromid=None, _id=None, toid=None, key=chr(949)):
        self.id = _id
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
    def __init__(self, status=None, a_status=None, b_status=None, c_status=None, d_status=None, is_end=False):
        self.end_status = is_end
        self.s = set(status)
        self.a = set(a_status) if a_status else set()
        self.b = set(b_status) if b_status else set()
        self.c = set(c_status) if c_status else set()
        self.d = set(d_status) if d_status else set()


class Fragment(object):
    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end

    def __repr__(self):
        return '(start={},end={})'.format(self.start.id, self.end.id)


class Token(object):
    def __init__(self):
        self.alphas = ['a', 'b', 'c', 'd']
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
        elif (token.is_left_brackets(char) or token.is_alpha(char)) and front_char == '*':
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
        fragment_1, fragment_2 = fragments[-2:]  # f_1 is front f_2 is back
        fragment_1.end.toid.append(fragment_2.start.id)  # f_1 end connect f_2 start
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
        status.append(NfaNode([fragment.end.id], status_index, None, chr(949)))  # s_2 = end
        fragment.end.toid.append(status_index)  # back 2 end
        status_index += 1
        status.append(NfaNode(None, status_index, [fragment.start.id, status[-1].id], chr(949)))  # s_1 = start
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
    nfa_fragments[-1].start.fromid.append(status_index)  # 原start的fromid加上新start的id
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


def closure(nfa_nodes, index, alpha, closure_list):
    if nfa_nodes[index].key != alpha:
        return
    else:
        for _id in nfa_nodes[index].toid:
            closure(nfa_nodes, _id, chr(949), closure_list)
            if _id not in closure_list:
                closure_list.append(_id)
    closure_list.sort()


def nfa2dfa(nfa_nodes, start_id, end_id):
    dfa_nodes, id_lists, initial_list = [], [], []
    closure(nfa_nodes, start_id, chr(949), initial_list)
    id_lists.append(initial_list)
    for id_list in id_lists:
        a_list, b_list, c_list, d_list = [], [], [], []
        for id_ in id_list:
            closure(nfa_nodes, id_, 'a', a_list)
            # a_list = delete_same(id_list, a_list)
            closure(nfa_nodes, id_, 'b', b_list)
            # b_list = delete_same(id_list, b_list)
            closure(nfa_nodes, id_, 'c', c_list)
            # c_list = delete_same(id_list, c_list)
            closure(nfa_nodes, id_, 'd', d_list)
            # d_list = delete_same(id_list, d_list)
        dfa_nodes.append(DfaNode(id_list, a_list, b_list, c_list, d_list, is_end(end_id, id_list)))
        list_in(a_list, id_lists)
        list_in(b_list, id_lists)
        list_in(c_list, id_lists)
        list_in(d_list, id_lists)
    for index in range(len(dfa_nodes)):
        for jndex in range(len(dfa_nodes)):
            if dfa_nodes[index].a == dfa_nodes[jndex].s:
                dfa_nodes[index].a = jndex
            if dfa_nodes[index].b == dfa_nodes[jndex].s:
                dfa_nodes[index].b = jndex
            if dfa_nodes[index].c == dfa_nodes[jndex].s:
                dfa_nodes[index].c = jndex
            if dfa_nodes[index].d == dfa_nodes[jndex].s:
                dfa_nodes[index].d = jndex
    print("\nNo.  a   b   c    d")
    for index in range(len(dfa_nodes)):
        print(str(index) + " " + str(dfa_nodes[index].a) + " " + str(dfa_nodes[index].b) + " " + str(dfa_nodes[index].c) + " " + str(dfa_nodes[index].d))
    return dfa_nodes


def delete_same(_list, to_list):
    if _list == to_list:
        to_list = []
    return to_list


def is_end(id_, list_):
    if id_ in list_:
        return True
    return False


def list_in(_list, id_lists):
    if _list and _list not in id_lists:
        id_lists.append(_list)


def dfa_show(dfa_nodes):
    f = Digraph(name="DFA", filename="DFA", format='png')
    f.attr(rankdir='LR', size='8,5')
    f.attr('node', shape='doublecircle')
    for index in range(len(dfa_nodes)):
        if dfa_nodes[index].end_status:
            f.node('{}'.format(str(index)))
    f.attr('node', shape='circle')
    for index in range(len(dfa_nodes)):
        if isinstance(dfa_nodes[index].a, int):
            f.edge("{}".format(str(index)), "{}".format(str(dfa_nodes[index].a)), label="a")
        if isinstance(dfa_nodes[index].b, int):
            f.edge("{}".format(str(index)), "{}".format(str(dfa_nodes[index].b)), label="b")
        if isinstance(dfa_nodes[index].c, int):
            f.edge("{}".format(str(index)), "{}".format(str(dfa_nodes[index].c)), label="c")
        if isinstance(dfa_nodes[index].d, int):
            f.edge("{}".format(str(index)), "{}".format(str(dfa_nodes[index].d)), label="d")
    f.view()


def nfa_show(fragments, status):
    f = Digraph(name="NFA", filename="NFA", format='png')
    f.attr(rankdir='LR', size='8,5')
    f.attr('node', shape='doublecircle')
    end_id = fragments[0].end.id
    f.node('{}'.format(str(end_id)))
    f.attr('node', shape='circle')
    for sta in status:
        for to_id in sta.toid:
            f.edge("{}".format(str(sta.id)), "{}".format(str(to_id)), label="{}".format(str(sta.key)))
    f.view()


def main():
    global token
    global status_index
    # input_string = input('>>')
    input_string = 'b(a|b)*a'
    # input_string = 'b*a(a|b)*'
    # input_string = '(ab)*(a*|b*)(ba)*'
    # input_string = 'a(a|b)cd'

    modify_string = "".join(modify_regex(input_string))
    # print(modify_string)

    suffix_string = suffixexp(modify_string)
    # print(suffix_string)
    fragments, nfa_nodes = to_nfa(suffix_string)
    nfa_show(fragments, nfa_nodes)  # test 1

    start_id = fragments[-1].start.id
    end_id = fragments[-1].end.id
    dfa_nodes = nfa2dfa(nfa_nodes, start_id, end_id)
    # print(dfa_nodes)
    dfa_show(dfa_nodes)


if __name__ == '__main__':
    main()
