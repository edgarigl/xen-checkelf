# xen-checkelf

xen-elfcheck is a tool that applies sanity checks on a Xen ELF file.
As of now, the only check done is to validate that the .init.text
section is consistent with what's in the .text section.

It will find functions in the .init.text section that get called from
the .text section (these are potentially harmful).

It will also find optimization opportunities with functions in the
.text section that are only called from the .init section.
These are not harmful but present an opportunity to optimize the
amount of runtime code for size and to increase the runtime heap.

## Limitations

xen-checkelf does not yet support following all references to functions.
This results in some false positives, in particular when function calls
are only made via function pointers. So you'll need to analyse the
source code before being sure that functions can be moved from .text
into .init.text.

# Install

## Pip install directly from git repo:
```bash
pip install git+ssh://git@github.com/edgarigl/xen-checkelf.git
```

## Developer mode

```bash
git clone https://github.com/edgarigl/xen-checkelf.git
cd xen-checkelf
pip install -e .
```

## Binutils
xen-checkelf depends on having binutils installed for the target
you're building Xen.

# Running

To get the best results, link Xen with the --emit-relocs flag.
E.g:
```bash
make XEN_TARGET_ARCH=arm64 build-xen LDFLAGS-y="--emit-relocs"
```

If the architecture you're building Xen for differs from your hosts
architecture, you'll need to use the --tools-prefix option to tell
xen-checkelf where to find the appropriate binutils. Here are some
examples:

Example on Xen/Aarch64 (Aarch64 host):
```console
$ xen-checkelf xen/xen-syms
OPTIMIZE assign_integer_param size=180
OPTIMIZE cpu_callback size=88
OPTIMIZE cpu_lockdebug_callback size=232
OPTIMIZE cpupool_check_granularity size=256
OPTIMIZE arm_smmu_id_size_to_bits size=92
OPTIMIZE arm_smmu_free_irqs size=112
OPTIMIZE arm_smmu_init_one_queue size=388
OPTIMIZE arm_smmu_update_gbpa size=260
OPTIMIZE va_to_par size=84
```

Example on Xen/x86 (Aarch64 host):
```console
$ xen-checkelf --tools-prefix=x86_64-linux-gnu- xen/xen-syms
OPTIMIZE assign_integer_param size=154
OPTIMIZE cpu_callback size=370
OPTIMIZE cpu_lockdebug_callback size=217
OPTIMIZE mtrr_check size=72
OPTIMIZE update_clusterinfo size=428
OPTIMIZE init_apic_ldr_x2apic_cluster size=458
OPTIMIZE get_apic_id size=30
OPTIMIZE cpu_nmi_callback size=136
OPTIMIZE write_cr4 size=71
OPTIMIZE vm_init size=34
OPTIMIZE no_config_param size=72
OPTIMIZE freq_string size=130
OPTIMIZE time_calibration size=131
OPTIMIZE plt_overflow size=290
BUG  amd_init_levelling
BUG  intel_init_levelling
BUG  calc_ler_msr
```
