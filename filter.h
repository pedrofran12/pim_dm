/* based on https://github.com/the-tcpdump-group/tcpdump */

#ifndef FILTER_H
#define FILTER_H

#define MAXIMUM_SNAPLEN    262144

#include <stdio.h>
#include <pcap.h>

int filter_try_compile(struct bpf_program *fp, const char *cmdbuf)
{
  int dump_dlt, ret;
  pcap_t *pd;

  dump_dlt = DLT_EN10MB;
  fprintf(stderr, "Warning: assuming Ethernet\n");
  pd = pcap_open_dead(dump_dlt, MAXIMUM_SNAPLEN);

  ret = pcap_compile(pd, fp, cmdbuf, 1, 0);
  if (ret < 0)
    fprintf(stderr, "%s", pcap_geterr(pd));

  pcap_close(pd);
  return (ret);
}

#endif /* FILTER_H */
