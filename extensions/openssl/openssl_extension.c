/*
 * (C) Copyright 2022
 *
 * SPDX-License-Identifier:     GPL-2.0-or-later
 */

/*
 * The library wraps OpenSSL client APIs
 */

#include <Python.h>

#include <openssl/x509v3.h>
#include <openssl/bn.h>
#include <openssl/asn1.h>
#include <openssl/x509.h>
#include <openssl/x509_vfy.h>
#include <openssl/pem.h>
#include <openssl/bio.h>
#include <openssl/pkcs12.h>
#include <openssl/opensslv.h>

#include <stdio.h>

#define DATE_LEN	128
#define EXTNAME_LEN	128

int convert_ASN1TIME(ASN1_TIME *t, char *buf, size_t len)
{
	int rc;
	BIO *b = BIO_new(BIO_s_mem());
	rc = ASN1_TIME_print(b, t);
	if (rc <= 0) {
		BIO_free(b);
		return EXIT_FAILURE;
	}
	rc = BIO_gets(b, buf, len);
	if (rc <= 0) {
		BIO_free(b);
		return EXIT_FAILURE;
	}
	BIO_free(b);
	return EXIT_SUCCESS;
}

static PyObject * get_cert_info(PyObject *self, PyObject *args)
{
	const char *path = NULL;
	const char *password = NULL;
	FILE *fp = NULL;
	X509 *cert = NULL;
	char *serial_number;
	char *subject;
	char *issuer;
	BIGNUM *serial_number_bn = NULL;
	int version = 0;
	ASN1_TIME *not_before;
	ASN1_TIME *not_after;
	char not_before_str[DATE_LEN];
	char not_after_str[DATE_LEN];
	STACK_OF(X509_EXTENSION) *exts = NULL;
	X509_EXTENSION *ex = NULL;
	ASN1_OBJECT *obj = NULL;
	int num_of_exts = -1;
	EVP_PKEY *pkey;
	STACK_OF(X509) *ca = NULL;
	PKCS12 *p12;
	PyObject *extensions_list = NULL;
	PyObject *result = NULL;

	if (!PyArg_ParseTuple(args, "z|z", &path, &password)) {
		PyErr_SetString(PyExc_RuntimeError, "get_cert_info: PyArg_ParseTuple failed");
		goto exit;
	}
	if (!(path && *path)) {
		PyErr_SetString(PyExc_RuntimeError, "get_cert_info: path is required");
		goto exit;
	}
	OpenSSL_add_all_algorithms();

	fp = fopen(path, "r");
	if (!fp) {
		PyErr_SetString(PyExc_RuntimeError, "get_cert_info: unable to open certificate");
		goto exit;
	}

	cert = PEM_read_X509(fp, NULL, NULL, NULL);
	if (!cert) {
		// Could not open the cert as a PEM, let's try DER
		rewind(fp);
		cert = d2i_X509_fp(fp, NULL);
		if (!cert) {
			// Could not open the cert as a DER either, let's try PKCS12
			if (!(password && *password)) {
				PyErr_SetString(PyExc_RuntimeError,
					"get_cert_info: PKCS certificate requires a password");
				goto exit;
			}
			rewind(fp);
			p12 = d2i_PKCS12_fp(fp, NULL);
			if (!p12) {
				PyErr_SetString(PyExc_RuntimeError,
					"get_cert_info: unable to read certificate");
				goto exit;
			}
			if (!PKCS12_parse(p12, password, &pkey, &cert, &ca)) {
				PyErr_SetString(PyExc_RuntimeError,
					"get_cert_info: unable to parse PKCS12 certificate");
				goto exit;
			}
			PKCS12_free(p12);
			if (!cert) {
				PyErr_SetString(PyExc_RuntimeError,
					"get_cert_info: unable to parse certificate");
				goto exit;
			}
		}
	}

	// Version is 0 indexed, so add 1 to normalize it
	version = ((int) X509_get_version(cert)) + 1;

	subject = X509_NAME_oneline(X509_get_subject_name(cert), NULL, 0);
	issuer = X509_NAME_oneline(X509_get_issuer_name(cert), NULL, 0);

	serial_number_bn = ASN1_INTEGER_to_BN(X509_get_serialNumber(cert), NULL);
	if (!serial_number_bn) {
		PyErr_SetString(PyExc_RuntimeError, "get_cert_info: unable to read serial number");
		goto exit;
	}

	serial_number = BN_bn2dec(serial_number_bn);
	if (!serial_number) {
		PyErr_SetString(PyExc_RuntimeError, "get_cert_info: unable to parse serial number");
		goto exit;
	}

	not_before = X509_get_notBefore(cert);
	not_after = X509_get_notAfter(cert);
	if (convert_ASN1TIME(not_before, not_before_str, DATE_LEN) == EXIT_FAILURE) {
		PyErr_SetString(PyExc_RuntimeError,
			"get_cert_info: unable to parse not before date");
		goto exit;
	}
	if (convert_ASN1TIME(not_after, not_after_str, DATE_LEN) == EXIT_FAILURE) {
		PyErr_SetString(PyExc_RuntimeError,
			"get_cert_info: unable to parse not after date");
		goto exit;
	}

#if OPENSSL_VERSION_NUMBER >= 0x10100000L
	exts = X509_get0_extensions(cert);
#else
	exts = cert->cert_info->extensions;
#endif
	num_of_exts = exts ? sk_X509_EXTENSION_num(exts) : 0;
	if (num_of_exts < 0) {
		PyErr_SetString(PyExc_RuntimeError, "get_cert_info: unable to parse extensions");
		goto exit;
	}
	extensions_list = PyList_New(num_of_exts);

	for (int i = 0; i < num_of_exts; i++) {
		ex = sk_X509_EXTENSION_value(exts, i);
		if (ex == NULL) {
			PyErr_SetString(PyExc_RuntimeError,
				"get_cert_info: unable to extract extension from stack");
			goto exit;
		}
		obj = X509_EXTENSION_get_object(ex);
		if (obj == NULL) {
			PyErr_SetString(PyExc_RuntimeError,
				"get_cert_info: unable to extract ASN1 object from extension");
			goto exit;
		}

		BIO *ext_bio = BIO_new(BIO_s_mem());
		if (ext_bio == NULL) {
			PyErr_SetString(PyExc_RuntimeError,
				"get_cert_info: unable to allocate memory for extension value BIO");
			goto exit;
		}
		if (!X509V3_EXT_print(ext_bio, ex, 0, 0)) {
#if OPENSSL_VERSION_NUMBER >= 0x10100000L
			ASN1_STRING_print(ext_bio, (ASN1_STRING *)X509_EXTENSION_get_data(ex));
#else
			ASN1_STRING_print(ext_bio, (ASN1_STRING *)ex->value);
#endif
		}

		BUF_MEM *bptr;
		BIO_get_mem_ptr(ext_bio, &bptr);
		BIO_set_close(ext_bio, BIO_NOCLOSE);
		BIO_free(ext_bio);

		// Decode data value string as UTF-8 using the 'replace' error handling method
		PyObject *value = PyUnicode_DecodeUTF8(bptr->data, bptr->length, "replace");
		if (value == NULL) {
			PyErr_SetString(PyExc_RuntimeError,
				"get_cert_info: unable to parse extension value");
			goto exit;

		}

		unsigned nid = OBJ_obj2nid(obj);
		if (nid == NID_undef) {
			// No lookup found for the provided OID so nid came back as undefined
			char extname[EXTNAME_LEN];
			OBJ_obj2txt(extname, EXTNAME_LEN, (const ASN1_OBJECT *) obj, 1);
			PyList_SET_ITEM(extensions_list,
				i,
				Py_BuildValue("{s:s,s:s}", "name", extname, "value", PyUnicode_AsUTF8(value)));
		} else {
			// The OID translated to a NID which implies that the OID has a known sn/ln
			const char *c_ext_name = OBJ_nid2ln(nid);
			if (c_ext_name == NULL) {
				Py_XDECREF(value);
				PyErr_SetString(PyExc_RuntimeError,
					"get_cert_info: invalid X509v3 extension name");
				goto exit;
			}
			PyList_SET_ITEM(extensions_list,
				i,
				Py_BuildValue("{s:s,s:s}", "name", c_ext_name, "value", PyUnicode_AsUTF8(value)));
		}
		Py_XDECREF(value);
	}

	result = Py_BuildValue("{s:i,s:s,s:s,s:s,s:s,s:s,s:O}",
		"version", version,
		"serial_number", serial_number,
		"subject", subject,
		"issuer", issuer,
		"not_before", not_before_str,
		"not_after", not_after_str,
		"extensions", extensions_list);
	Py_XDECREF(extensions_list);

exit:
	if (ca)
		sk_X509_pop_free(ca, X509_free);
	if (cert)
		X509_free(cert);
	if (serial_number_bn)
		BN_free(serial_number_bn);
	if (fp)
		fclose(fp);

	return result;
}

static PyMethodDef openssl_extension_methods[] =
{
	{ "get_cert_info",		get_cert_info,  METH_VARARGS, "Return the basic information about a certificate"	},
	{ NULL,			NULL,		    0,		  NULL				     }
};

// The arguments of this structure tell Python what to call your extension,
// what it's methods are and where to look for it's method definitions
static struct PyModuleDef openssl_extension_definition =
{
	PyModuleDef_HEAD_INIT,
	"openssl_extension",
	"A Python module that wraps OpenSSL APIs.",
	-1,
	openssl_extension_methods
};

PyMODINIT_FUNC PyInit_openssl_extension(void)
{
	return PyModule_Create(&openssl_extension_definition);
}
