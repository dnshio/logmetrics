from typing_extensions import Callable
from sqlalchemy import create_engine, Table


# from bytewax.outputs import FixedPartitionedSink, StatefulSinkPartition
from bytewax.outputs import StatelessSinkPartition, DynamicSink


class TableSink(DynamicSink):
    def __init__(
        self,
        dsn: str,
        table: Table,
        value_generator: Callable,
        reset_table=True,
    ):
        self.dsn = dsn
        self.table = table
        self.value_generator = value_generator
        self.reset_table = reset_table

    def build(self, step_id, worker_index, worker_count):
        return TableSinkPartition(
            self.dsn, self.table, self.value_generator, self.reset_table
        )


class TableSinkPartition(StatelessSinkPartition):
    def __init__(
        self,
        dsn,
        table: Table,
        value_generator: Callable,
        reset_table=True,
    ):
        self.dsn = dsn
        self.table = table
        self.value_generator = value_generator

        self.engine = create_engine(dsn)

        if reset_table:
            self.reset_table()

    def reset_table(self):
        self.table.metadata.drop_all(self.engine)
        self.table.metadata.create_all(self.engine)

    def write_batch(self, items):
        with self.engine.connect() as conn:
            for item in items:
                conn.execute(self.table.insert().values(**self.value_generator(item)))

            conn.commit()

    def close(self):
        pass
