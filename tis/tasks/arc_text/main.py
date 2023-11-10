import os
import faker
from tqdm import tqdm
from .label import save_data
from _appdir import OUTPUT_DIR


def main(batch):
    output_dir = os.path.join(OUTPUT_DIR, "arc_text")
    f = faker.Faker(providers=["provider"])
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    cnt = 0
    pbar = tqdm(total=batch)
    pbar.set_description("Generating")
    while cnt < batch:
        data = f.image()
        save_data(data, output_dir)
        cnt += 1
        pbar.update(1)
    pbar.close()


if __name__ == "__main__":
    main(2)
