// SPDX-License-Identifier: GPL-2.0-only
/* eurephia_nullsafe.c
 *
 *  standard C string functions, which is made NULL safe by checking
 *  if input value is NULL before performing the action.
 *
 *  This version is modified to work outside the eurephia project.
 *
 *  GPLv2 only - Copyright (C) 2009
 *               David Sommerseth <dazo@users.sourceforge.net>
 *
 */

/**
 * @file   eurephia_nullsafe.c
 * @author David Sommerseth <dazo@users.sourceforge.net>
 * @date   2009-09-07
 *
 * @brief standard C string functions, which is made NULL safe by checking
 *        if input value is NULL before performing the action.
 *
 */

#include <stdio.h>
#include <stdlib.h>

#include <log.h>

#if __GNUC__ >= 3
#define __malloc__ __attribute__((malloc))
#else /* If not GCC 3 or newer, disable optimisations */
#define __malloc__
#endif

/**
 * This replaces the use of malloc() and memset().  This function uses calloc
 * internally, which results in the memory region being zero'd by the kernel
 * on memory allocation.
 *
 * @param log   Log context
 * @param sz    size of the memory region being allocated
 *
 * @return Returns a void pointer to the memory region on success, otherwise NULL
 */
__malloc__ void *malloc_nullsafe(LogContext *log, size_t sz) {
        void *buf = NULL;

        buf = calloc(1, sz);    /* Using calloc, also gives a zero'd memory region */
        if( !buf ) {
		writelog(log, LOG_EMERG, "Could not allocate memory region for %ld bytes", sz);
		exit(9);
        }
        return buf;
}
