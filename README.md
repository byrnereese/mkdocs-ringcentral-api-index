# mkdocs-minify-plugin

A MkDocs plugin created by RingCentral to assist in the creation of its Mkdocs powered developer guide.

At RingCentral we had the desire to publish an API Quick Reference that would make it easier for developers to scan for the endpoint they are looking for and quickly access the documentation for that endpoint in our API Reference. 

## Setup

Install the plugin using pip:

`pip install mkdocs-ringcentral-api-index-plugin`

Activate the plugin in `mkdocs.yml`:
```yaml
plugins:
  - search
  - rc-api-index:
      spec_url: true
      outfile: 'docs/api-index.md'
```

> **Note:** If you have no `plugins` entry in your config file yet, you'll likely also want to add the `search` plugin. MkDocs enables it by default if there is no `plugins` entry set, but now you have to enable it explicitly.

## Options

- `spec_url`: Sets the URL to the Swagger specification for the RingCentral platform. This should default to the official URL. Override this for development purposes only. 
- `outfile`: The file to output. This file is typically somewhere in your docs folder. 

More information about plugins in the [MkDocs documentation][mkdocs-plugins].

## See Also

More information about templates [here][mkdocs-template].

More information about blocks [here][mkdocs-block].

[mkdocs-plugins]: https://www.mkdocs.org/user-guide/plugins/
[mkdocs-template]: https://www.mkdocs.org/user-guide/custom-themes/#template-variables
[mkdocs-block]: https://www.mkdocs.org/user-guide/styling-your-docs/#overriding-template-blocks
