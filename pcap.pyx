#include <pcap.h>

import struct

ctypedef unsigned int u_int
ctypedef unsigned char u_char
ctypedef unsigned short int u_short
ctypedef u_int bpf_u_int32

cdef extern from "pcap.h":
    struct bpf_insn:
        u_short code
        u_char jt
        u_char jf
        bpf_u_int32 k
    struct bpf_program:
        bpf_insn *bf_insns
        u_int bf_len

cdef extern from "pcap.h":
    void    pcap_freecode(bpf_program *fp)

cdef extern from "filter.h":
    int    filter_try_compile(bpf_program *fp, const char *cmdbuf)


cdef class bpf:
    """bpf(filter) -> BPF filter object"""

    cdef bpf_program fcode

    def __init__(self, char *filter):
        if filter_try_compile(&self.fcode, filter) < 0:
            raise IOError, 'bad filter'

    def compiled_filter(self):
        cdef bpf_insn *bf_insns
        bf_insns = self.fcode.bf_insns
        size = self.fcode.bf_len

        return size, b''.join(
            struct.pack('HBBI', bf_insns[i].code, bf_insns[i].jt, bf_insns[i].jf, bf_insns[i].k)
            for i in range(size)
        )

    def dump(self):
        cdef bpf_insn *bf_insns
        cdef bpf_insn bf_insn
        bf_insns = self.fcode.bf_insns
        for i in range(self.fcode.bf_len):
            bf_insn = bf_insns[i]
            print("{ 0x%x, %d, %d, 0x%08x }," % (bf_insn.code, bf_insn.jt, bf_insn.jf, bf_insn.k))

    def __dealloc__(self):
        pcap_freecode(&self.fcode)
