/* SPDX-License-Identifier: GPL-2.0-only */
/* eurephia_values.h  --  eurephiaVALUES struct typedef
 *
 *  GPLv2 only - Copyright (C) 2008
 *               David Sommerseth <dazo@users.sourceforge.net>
 *
 */

/**
 * @file   eurephia_values_struct.h
 * @author David Sommerseth <dazo@users.sourceforge.net>
 * @date   2008-11-05
 *
 * @brief  Definition of the eurephiaVALUES struct
 *
 */

#ifndef   	EUREPHIA_VALUES_STRUCT_H_
# define   	EUREPHIA_VALUES_STRUCT_H_

#include <log.h>

/**
 * eurephiaVALUES is a pointer chain with key/value pairs.  If having several
 * such pointer chains, they can be given different group IDs to separate them,
 * which is especially useful during debugging.
 *
 */
typedef struct __eurephiaVALUES {
	LogContext *log;        /**< Pointer to an established log context, used for logging */
        unsigned int evgid;	/**< Group ID, all elements in the same chain should have the same value */
        unsigned int evid;	/**< Unique ID per element in a pointer chain */
        char *key;		/**< The key name of a value */
        char *val;		/**< The value itself */
        struct __eurephiaVALUES *next; /**< Pointer to the next element in the chain. NULL == end of chain */
} eurephiaVALUES;

#endif 	    /* !EUREPHIA_VALUES_STRUCT_H_ */
