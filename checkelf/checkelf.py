#!/usr/bin/env python3
#
# Copyright (c) 2024 Advanced Micro Devices, Inc.
# Written by Edgar E. Iglesias <edgar.iglesias@amd.com>
#
# SPDX-License-Identifier: MIT
#
"""
ELF Checker for Xen.
"""
import argparse
import subprocess

def run(cmd):
    """
    Run a comment and return the subprocess.
    """
    p = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, text=True)
    return p

class sym:
    """
    Class representing a symbol.
    """
    def __init__(self, name, addr, size, kind):
        self.name = name
        self.addr = addr
        self.size = size
        self.kind = kind

class symtab:
    """
    Class representing a symbol-table.
    """
    def __init__(self):
        self.tab = {}

    def add(self, s: sym):
        """
        Add a symbol to the symbol table.
        """
        self.tab[s.name] = s

    def get(self, name: str):
        """
        Get a symbol from the symbol table.
        """
        r = None
        try:
            r = self.tab[name]
        except:
            pass
        return r

class elfmap:
    """
    Class representing an ELF file.
    """
    def __init__(self, elf, tools_prefix='', verbose=False):
        self.elf = elf
        self.tools_prefix = tools_prefix
        self.verbose = verbose
        self.symtab = {}
        self.callmap = {}
        self.create_symtab(section='.text')
        self.create_symtab(section='.init.text')
        self.create_callmap(section='.text')
        self.create_callmap(section='.init.text')

        for n in self.symtab['.text'].tab.keys():
            called_by_text = n in self.callmap['.text']
            called_by_init = n in self.callmap['.init.text']
            if called_by_init and not called_by_text:
                s = self.symtab['.text'].get(n)
                print(f'OPTIMIZE {n} size={s.size:d}')

        for n in self.symtab['.init.text'].tab.keys():
            called_by_text = n in self.callmap['.text']
            called_by_init = n in self.callmap['.init.text']
            if called_by_text and n not in self.symtab['.text'].tab.keys():
                print("BUG ", n)

    def insn_is_call(self, insn):
        """
        Check if a given insn is a function call.
        """
        if insn == "bl":
            return True
        if insn == "call":
            return True
        return False

    def create_callmap(self, section):
        """
        Create a list of called functions from a given section.
        """
        self.callmap[section] = []
        c = run(cmd=[self.tools_prefix + 'objdump',
                     '-Dr', '-j', section, self.elf])

        for line in c.stdout.splitlines():
            tokens = line.split()
            insn_idx = len(tokens) - 3
            sym_idx = len(tokens) - 1
            if len(tokens) >= 5 and self.insn_is_call(tokens[insn_idx]):
                name = tokens[sym_idx].strip('<>')

                s = self.symtab['.text'].get(name)
                if s is None and section == '.text':
                    s = self.symtab['.init.text'].get(name)

                if self.verbose:
                    print(f'callmap {section}: {name}')
                self.callmap[section].append(name)


    def create_symtab(self, section):
        """
        Populate the symbol-table.
        """
        self.symtab[section] = symtab()

        c = run(cmd=[self.tools_prefix + 'objdump',
                     '-t', '-j', section, self.elf])
        for line in c.stdout.splitlines():
            tokens = line.split()
            if len(tokens) >= 6:
                try:
                    addr = int(tokens[0], 16)
                    size = int(tokens[4], 16)
                    s = sym(name=tokens[5],
                            addr=addr,
                            size=size,
                            kind=tokens[2])
                    self.symtab[section].add(s)
                    if self.verbose:
                        print(f'symtab[{section}]: {s.name}')
                except Exception as e:
                    # print(e)
                    pass


def checkelf_main():
    """
    Entry point for the checkelf application.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--tools-prefix', type=str, default='',
                        help="Binutils prefix")
    parser.add_argument('--verbose', action='store_true', default=False,
                        help="Verbose mode")
    parser.add_argument('elf', help="ELF filename")

    args = parser.parse_args()

    elfmap(elf=args.elf,
           tools_prefix=args.tools_prefix,
           verbose=args.verbose)
