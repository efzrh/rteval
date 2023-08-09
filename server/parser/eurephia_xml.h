/* SPDX-License-Identifier: GPL-2.0-only */
/* eurephia_xml.h  --  Generic helper functions for XML parsing
 *
 * This version is modified to work outside the eurephia project.
 *
 *  GPLv2 only - Copyright (C) 2008
 *               David Sommerseth <dazo@users.sourceforge.net>
 *
 */

/**
 * @file   eurephia_xml.h
 * @author David Sommerseth <dazo@users.sourceforge.net>
 * @date   2008-12-15
 *
 * @brief  Generic XML parser functions
 *
 */


#ifndef   	EUREPHIA_XML_H_
#define   	EUREPHIA_XML_H_

#include <stdarg.h>

#include <libxml/tree.h>

/**
 * Simple iterator macro for iterating xmlNode pointers
 *
 * @param start  Pointer to an xmlNode where to start iterating
 * @param itn    An xmlNode pointer which will be used for the iteration.
 */
#define foreach_xmlnode(start, itn)  for( itn = start; itn != NULL; itn = itn->next )

char *xmlGetAttrValue(xmlAttr *properties, const char *key);
xmlNode *xmlFindNode(xmlNode *node, const char *key);

inline char *xmlExtractContent(xmlNode *n);
inline char *xmlGetNodeContent(xmlNode *node, const char *key);
char *xmlNodeToString(LogContext *log, xmlNode *node);

#endif 	    /* !EUREPHIA_XML_H_ */
