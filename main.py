import click

import zjsn_uncensor


@click.group()
def cli():
    pass


@cli.command()
def mitm():
    zjsn_uncensor.MITMproxy.run.main()


@cli.command()
def static():
    zjsn_uncensor.static_server.app.main()


@cli.command()
def get_data():
    zjsn_uncensor.static_server.get_data.ResourceDownloader().run()


cli.add_command(mitm)
cli.add_command(static)
cli.add_command(get_data)
cli()
